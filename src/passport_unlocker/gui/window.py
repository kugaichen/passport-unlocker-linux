from typing import Any

from passport_unlocker.devices.discovery import list_candidate_devices
from passport_unlocker.devices.identity import DeviceIdentity

from .runner import PrivilegedRunner


def _format_size(size: int) -> str:
    return f"{size / (1024**3):.1f} GiB" if size else "Unknown size"


def create_window_class() -> type[Any]:
    from gi.repository import Adw, Gtk

    class PassportWindow(Adw.ApplicationWindow):
        def __init__(self, application: Any) -> None:
            super().__init__(application=application, title="Passport Unlocker")
            self.set_default_size(520, 360)
            self._devices: list[DeviceIdentity] = []
            self._runner = PrivilegedRunner()

            layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            layout.append(Adw.HeaderBar())
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
            content.set_margin_top(24)
            content.set_margin_bottom(24)
            content.set_margin_start(24)
            content.set_margin_end(24)
            layout.append(content)
            self.set_content(layout)

            title = Gtk.Label(label="Unlock a compatible WD My Passport drive")
            title.add_css_class("title-2")
            content.append(title)
            self._device = Gtk.DropDown.new_from_strings(["No compatible device found"])
            content.append(self._device)
            self._password = Gtk.PasswordEntry(
                show_peek_icon=True,
                placeholder_text="Drive password",
            )
            content.append(self._password)
            self._unlock = Gtk.Button(label="Unlock drive")
            self._unlock.add_css_class("suggested-action")
            self._unlock.connect("clicked", self._on_unlock)
            self._password.connect("activate", self._on_unlock)
            content.append(self._unlock)
            self._status = Gtk.Label(label="Connect a compatible encrypted drive.", wrap=True)
            content.append(self._status)
            disclaimer = Gtk.Label(
                label="Unofficial utility. Not affiliated with or endorsed by Western Digital.",
                wrap=True,
            )
            disclaimer.add_css_class("dim-label")
            content.append(disclaimer)
            self.refresh_devices()

        def refresh_devices(self, present: bool = False) -> None:
            previous = {item.stable_id for item in self._devices}
            self._devices = list_candidate_devices()
            labels = [
                f"{item.display_name} · {_format_size(item.size_bytes)} · …{item.serial_suffix}"
                for item in self._devices
            ] or ["No compatible device found"]
            self._device.set_model(Gtk.StringList.new(labels))
            self._unlock.set_sensitive(bool(self._devices))
            if present and ({item.stable_id for item in self._devices} - previous):
                self.present()

        def _on_unlock(self, _button: Any) -> None:
            selected = self._device.get_selected()
            password = self._password.get_text()
            if selected >= len(self._devices) or not password:
                self._status.set_label("Select a drive and enter its password.")
                return
            self._unlock.set_sensitive(False)
            self._password.set_sensitive(False)
            self._status.set_label("Requesting system authorization and unlocking…")
            self._password.set_text("")
            self._runner.unlock(self._devices[selected].stable_id, password, self._on_result)

        def _on_result(self, result: dict[str, Any]) -> bool:
            messages = {
                "wrong_password": "The drive password is incorrect.",
                "unlock_blocked": "The drive blocks further attempts. Safely reconnect it.",
                "permission_denied": "System authorization was cancelled or denied.",
                "device_disconnected": "The drive was disconnected during the operation.",
                "unsupported_device": "This device protocol is not supported.",
                "protocol_signature": "The device returned an incompatible response.",
                "rescan_timeout": "Unlocked, but Linux did not rediscover the drive in time.",
                "helper_timeout": "The privileged operation timed out.",
            }
            if result.get("ok"):
                self._status.set_label("Drive unlocked. It should now appear in the file manager.")
            else:
                code = str(result.get("error_code", "helper_failed"))
                self._status.set_label(messages.get(code, "The drive could not be unlocked."))
            self._password.set_sensitive(True)
            self._unlock.set_sensitive(bool(self._devices))
            self.refresh_devices()
            return False

    return PassportWindow
