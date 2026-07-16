from dataclasses import dataclass
from hashlib import sha256


def _clean(value: str) -> str:
    return " ".join(value.replace("_", " ").split())


def make_stable_id(usb_vid: str, usb_pid: str, serial: str, model: str) -> str:
    fields = (usb_vid.lower(), usb_pid.lower(), serial.strip(), _clean(model).lower())
    if not all(fields):
        raise ValueError("Stable identity requires VID, PID, serial and model")
    return sha256(":".join(fields).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class DeviceIdentity:
    stable_id: str
    device_node: str
    sys_name: str
    sys_path: str
    model: str
    vendor: str
    serial: str
    size_bytes: int
    usb_vid: str
    usb_pid: str
    scsi_host: str | None = None

    @property
    def serial_suffix(self) -> str:
        return self.serial[-4:].rjust(4, "•")

    @property
    def display_name(self) -> str:
        return _clean(self.model)

