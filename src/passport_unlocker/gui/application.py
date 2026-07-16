import sys
from typing import Any

APP_ID = "io.github.kugaichen.PassportUnlocker"


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    try:
        import gi

        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Adw, Gio
    except (ImportError, ValueError):
        print("GTK 4 and Libadwaita are required to run the GUI.", file=sys.stderr)
        return 1

    from passport_unlocker.devices.monitor import DeviceMonitor

    from .window import create_window_class

    Window = create_window_class()

    class Application(Adw.Application):
        def __init__(self) -> None:
            super().__init__(
                application_id=APP_ID,
                flags=Gio.ApplicationFlags.HANDLES_COMMAND_LINE,
            )
            self._window: Any | None = None
            self._monitor: DeviceMonitor | None = None

        def _ensure_window(self) -> None:
            if self._window is None:
                self._window = Window(self)
                self._monitor = DeviceMonitor(lambda: self._window.refresh_devices(True))
                self._monitor.start()

        def do_activate(self) -> None:
            self._ensure_window()
            self._window.present()

        def do_command_line(self, command_line: Any) -> int:
            arguments = command_line.get_arguments()
            is_monitor = "--monitor" in arguments
            self._ensure_window()
            if is_monitor:
                self.hold()
                if self._window._devices:
                    self._window.present()
            else:
                self._window.present()
            return 0

    return Application().run(argv)


if __name__ == "__main__":
    raise SystemExit(main())
