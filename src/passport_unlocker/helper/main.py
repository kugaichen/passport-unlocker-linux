import argparse
import os
import sys
from typing import Any

from passport_unlocker.core.errors import (
    DeviceDisconnectedError,
    DeviceNotFoundError,
    PassportUnlockerError,
    PermissionDeniedError,
    ProtocolResponseError,
    ProtocolSignatureError,
    RescanError,
    RescanTimeoutError,
    ScsiTransportError,
    UnlockBlockedError,
    UnsupportedDeviceError,
    WrongPasswordError,
)
from passport_unlocker.core.linux_sg_io import LinuxSgIoTransport
from passport_unlocker.core.protocol import WdPassportProtocol
from passport_unlocker.devices.discovery import find_by_stable_id
from passport_unlocker.devices.rescan import rescan_device, wait_for_device

from .validation import validate_block_device, validate_stable_id
from .wire import WireProtocolError, read_password, write_result

ERROR_CODES: list[tuple[type[BaseException], str]] = [
    (WrongPasswordError, "wrong_password"),
    (UnlockBlockedError, "unlock_blocked"),
    (PermissionDeniedError, "permission_denied"),
    (DeviceDisconnectedError, "device_disconnected"),
    (DeviceNotFoundError, "device_not_found"),
    (UnsupportedDeviceError, "unsupported_device"),
    (ProtocolSignatureError, "protocol_signature"),
    (ProtocolResponseError, "protocol_error"),
    (RescanTimeoutError, "rescan_timeout"),
    (RescanError, "rescan_error"),
    (ScsiTransportError, "scsi_error"),
    (WireProtocolError, "invalid_input"),
    (PassportUnlockerError, "application_error"),
]


def _error_code(exc: BaseException) -> str:
    return next(
        (code for error_type, code in ERROR_CODES if isinstance(exc, error_type)),
        "internal_error",
    )


def _result(ok: bool, operation: str, stable_id: str, **values: Any) -> dict[str, Any]:
    return {"ok": ok, "operation": operation, "stable_id": stable_id[:12], **values}


def run(operation: str, stable_id: str, stdin: Any = None) -> dict[str, Any]:
    if os.geteuid() != 0:
        raise PermissionDeniedError("The privileged helper must run through Polkit")
    validate_stable_id(stable_id)
    identity = find_by_stable_id(stable_id)
    validate_block_device(identity)

    if operation == "status":
        with LinuxSgIoTransport(identity.device_node) as transport:
            status = WdPassportProtocol(transport).get_status()
        return _result(True, operation, stable_id, state=status.state.name.lower())

    password_bytes = read_password(stdin or sys.stdin.buffer)
    try:
        password = password_bytes.decode("utf-8")
        with LinuxSgIoTransport(identity.device_node) as transport:
            protocol = WdPassportProtocol(transport)
            before = protocol.get_status()
            after = protocol.unlock(password)
        rescan_device(identity)
        rediscovered = wait_for_device(stable_id)
        return _result(
            True,
            operation,
            stable_id,
            state_before=before.state.name.lower(),
            state_after=after.state.name.lower(),
            device_node=rediscovered.device_node,
            rescanned=True,
        )
    finally:
        for index in range(len(password_bytes)):
            password_bytes[index] = 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="passport-unlocker-helper")
    parser.add_argument("operation", choices=("status", "unlock-and-rescan"))
    parser.add_argument("--stable-id", required=True)
    args = parser.parse_args(argv)
    try:
        result = run(args.operation, args.stable_id)
        exit_code = 0
    except Exception as exc:
        code = _error_code(exc)
        message = "The requested operation could not be completed"
        result = _result(False, args.operation, args.stable_id, error_code=code, message=message)
        exit_code = 40 if code == "internal_error" else 1
    write_result(sys.stdout, result)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
