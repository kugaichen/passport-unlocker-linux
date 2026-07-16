import re
import time
from pathlib import Path
from typing import Any

from passport_unlocker.core.errors import DeviceNotFoundError, RescanError, RescanTimeoutError

from .discovery import find_by_stable_id
from .identity import DeviceIdentity

_DISK_NAME = re.compile(r"sd[a-z]+\Z")
_HOST_NAME = re.compile(r"host\d+\Z")


def rescan_device(identity: DeviceIdentity, sys_root: Path = Path("/sys")) -> None:
    if not _DISK_NAME.fullmatch(identity.sys_name) or not identity.scsi_host:
        raise RescanError("Device has no validated SCSI disk/host identity")
    if not _HOST_NAME.fullmatch(identity.scsi_host):
        raise RescanError("SCSI host name is invalid")
    delete_path = sys_root / "block" / identity.sys_name / "device" / "delete"
    scan_path = sys_root / "class" / "scsi_host" / identity.scsi_host / "scan"
    try:
        delete_path.write_text("1\n", encoding="ascii")
        scan_path.write_text("- - -\n", encoding="ascii")
    except OSError as exc:
        raise RescanError("Kernel device rescan failed") from exc


def wait_for_device(
    stable_id: str,
    timeout: float = 15.0,
    context: Any | None = None,
) -> DeviceIdentity:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            return find_by_stable_id(stable_id, context)
        except DeviceNotFoundError:
            pass
        time.sleep(0.25)
    raise RescanTimeoutError("Device did not reappear before timeout")
