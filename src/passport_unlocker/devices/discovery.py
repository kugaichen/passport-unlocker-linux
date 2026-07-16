from collections.abc import Iterable
from typing import Any

from passport_unlocker.core.errors import DeviceNotFoundError

from .identity import DeviceIdentity, make_stable_id


def _parents(device: Any) -> Iterable[Any]:
    current = device
    while current is not None:
        yield current
        current = getattr(current, "parent", None)


def _property(device: Any, name: str) -> str:
    for item in _parents(device):
        properties = getattr(item, "properties", {})
        value = properties.get(name)
        if value:
            return str(value)
    return ""


def _size_bytes(device: Any) -> int:
    attributes = getattr(device, "attributes", None)
    if attributes is None:
        return 0
    try:
        sectors = attributes.get("size")
        if isinstance(sectors, bytes):
            sectors = sectors.decode("ascii")
        return int(sectors or 0) * 512
    except (TypeError, ValueError, OSError):
        return 0


def _scsi_host(device: Any) -> str | None:
    finder = getattr(device, "find_parent", None)
    if finder is None:
        return None
    try:
        parent = finder(subsystem="scsi", device_type="scsi_host")
    except (AttributeError, OSError):
        return None
    return str(parent.sys_name) if parent is not None else None


def identity_from_device(device: Any) -> DeviceIdentity | None:
    if getattr(device, "device_node", None) is None:
        return None
    properties = getattr(device, "properties", {})
    if str(properties.get("DEVTYPE", "")) != "disk":
        return None

    vendor = _property(device, "ID_VENDOR")
    model = _property(device, "ID_MODEL")
    serial = _property(device, "ID_SERIAL_SHORT") or _property(device, "ID_SERIAL")
    vid = _property(device, "ID_VENDOR_ID")
    pid = _property(device, "ID_MODEL_ID")
    bus = _property(device, "ID_BUS")
    normalized_vendor = vendor.replace("_", " ").lower()
    normalized_model = model.replace("_", " ").lower()

    if bus.lower() != "usb":
        return None
    if not (
        normalized_vendor in {"wd", "western digital"}
        or "western digital" in normalized_vendor
    ):
        return None
    if "passport" not in normalized_model:
        return None
    if not all((serial, vid, pid, model)):
        return None

    stable_id = make_stable_id(vid, pid, serial, model)
    return DeviceIdentity(
        stable_id=stable_id,
        device_node=str(device.device_node),
        sys_name=str(device.sys_name),
        sys_path=str(device.sys_path),
        model=model,
        vendor=vendor,
        serial=serial,
        size_bytes=_size_bytes(device),
        usb_vid=vid,
        usb_pid=pid,
        scsi_host=_scsi_host(device),
    )


def list_candidate_devices(context: Any | None = None) -> list[DeviceIdentity]:
    if context is None:
        import pyudev

        context = pyudev.Context()
    identities = []
    for device in context.list_devices(subsystem="block", DEVTYPE="disk"):
        identity = identity_from_device(device)
        if identity is not None:
            identities.append(identity)
    return sorted(identities, key=lambda item: (item.display_name.lower(), item.serial_suffix))


def find_by_stable_id(stable_id: str, context: Any | None = None) -> DeviceIdentity:
    matches = [item for item in list_candidate_devices(context) if item.stable_id == stable_id]
    if len(matches) != 1:
        raise DeviceNotFoundError("Stable device identity did not resolve uniquely")
    return matches[0]
