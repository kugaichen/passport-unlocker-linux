import json
import subprocess
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from passport_unlocker.helper.wire import encode_password

PKEXEC = "/usr/bin/pkexec"
HELPER = "/usr/libexec/passport-unlocker-helper"


class PrivilegedRunner:
    def __init__(self) -> None:
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="passport-helper")

    @staticmethod
    def _invoke(stable_id: str, password: str) -> dict[str, Any]:
        try:
            process = subprocess.Popen(
                [PKEXEC, HELPER, "unlock-and-rescan", "--stable-id", stable_id],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            return {"ok": False, "error_code": "helper_failed"}
        try:
            stdout, _ = process.communicate(encode_password(password), timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            return {"ok": False, "error_code": "helper_timeout"}
        try:
            result = json.loads(stdout.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {"ok": False, "error_code": "helper_failed"}
        return result if isinstance(result, dict) else {"ok": False, "error_code": "helper_failed"}

    def unlock(
        self,
        stable_id: str,
        password: str,
        callback: Callable[[dict[str, Any]], None],
    ) -> None:
        from gi.repository import GLib

        future = self._executor.submit(self._invoke, stable_id, password)

        def complete(item: Any) -> None:
            try:
                result = item.result()
            except Exception:
                result = {"ok": False, "error_code": "helper_failed"}
            GLib.idle_add(callback, result)

        future.add_done_callback(complete)
