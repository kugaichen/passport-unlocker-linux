from collections.abc import Callable
from typing import Any


class DeviceMonitor:
    def __init__(self, callback: Callable[[], None], debounce_ms: int = 900) -> None:
        import pyudev
        from gi.repository import GLib

        self._callback = callback
        self._debounce_ms = debounce_ms
        self._glib = GLib
        self._pending_source = 0
        monitor = pyudev.Monitor.from_netlink(pyudev.Context())
        monitor.filter_by(subsystem="block")
        self._observer = pyudev.MonitorObserver(monitor, callback=self._event)

    def _event(self, _action: str, _device: Any) -> None:
        self._glib.idle_add(self._schedule)

    def _schedule(self) -> bool:
        if self._pending_source:
            self._glib.source_remove(self._pending_source)
        self._pending_source = self._glib.timeout_add(self._debounce_ms, self._fire)
        return False

    def _fire(self) -> bool:
        self._pending_source = 0
        self._callback()
        return False

    def start(self) -> None:
        self._observer.start()

    def stop(self) -> None:
        self._observer.stop()

