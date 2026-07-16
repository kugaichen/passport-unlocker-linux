import argparse
import getpass
import json
import subprocess
import sys

from passport_unlocker import __version__
from passport_unlocker.devices.discovery import list_candidate_devices
from passport_unlocker.helper.wire import encode_password

PKEXEC = "/usr/bin/pkexec"
HELPER = "/usr/libexec/passport-unlocker-helper"


def _helper(operation: str, stable_id: str, password: str | None = None) -> dict[str, object]:
    argv = [PKEXEC, HELPER, operation, "--stable-id", stable_id]
    input_data = encode_password(password) if password is not None else None
    completed = subprocess.run(argv, input=input_data, capture_output=True, check=False)
    try:
        return json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {"ok": False, "error_code": "helper_failed"}


def _print_devices() -> int:
    devices = list_candidate_devices()
    for device in devices:
        gib = device.size_bytes / (1024**3)
        print(f"{device.stable_id}  {device.display_name}  {gib:.1f} GiB  …{device.serial_suffix}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="passport-unlocker")
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("list")
    for command in ("status", "unlock"):
        subparser = subparsers.add_parser(command)
        subparser.add_argument("--device-id", required=True)
    args = parser.parse_args(argv)
    if args.command == "list":
        return _print_devices()
    password = getpass.getpass("Drive password: ") if args.command == "unlock" else None
    operation = "unlock-and-rescan" if args.command == "unlock" else "status"
    result = _helper(operation, args.device_id, password)
    if result.get("ok"):
        print(result.get("state_after", result.get("state", "ok")))
        return 0
    print(f"Error: {result.get('error_code', 'unknown_error')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

