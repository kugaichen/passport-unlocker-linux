import os
import re
import stat
from collections.abc import Callable

from passport_unlocker.core.errors import DeviceIdentityChangedError
from passport_unlocker.devices.identity import DeviceIdentity

_STABLE_ID = re.compile(r"[0-9a-f]{64}\Z")


def validate_stable_id(stable_id: str) -> None:
    if not _STABLE_ID.fullmatch(stable_id):
        raise DeviceIdentityChangedError("Stable device identity is invalid")


def validate_block_device(
    identity: DeviceIdentity,
    lstat_fn: Callable[[str], os.stat_result] = os.lstat,
) -> None:
    validate_stable_id(identity.stable_id)
    if not identity.device_node.startswith("/dev/") or os.path.islink(identity.device_node):
        raise DeviceIdentityChangedError("Device node is not a direct /dev block path")
    try:
        mode = lstat_fn(identity.device_node).st_mode
    except OSError as exc:
        raise DeviceIdentityChangedError("Device node is unavailable") from exc
    if not stat.S_ISBLK(mode):
        raise DeviceIdentityChangedError("Device node is not a block device")
    if not all((identity.usb_vid, identity.usb_pid, identity.serial, identity.model)):
        raise DeviceIdentityChangedError("USB identity is incomplete")

