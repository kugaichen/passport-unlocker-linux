import unittest

from passport_unlocker.devices.identity import DeviceIdentity, make_stable_id


class IdentityTests(unittest.TestCase):
    def test_device_node_is_not_part_of_stable_id(self) -> None:
        first = make_stable_id("1058", "2626", "SERIAL-A", "My Passport 2626")
        second = make_stable_id("1058", "2626", "SERIAL-A", "My_Passport_2626")
        self.assertEqual(first, second)

    def test_only_serial_suffix_is_for_display(self) -> None:
        identity = DeviceIdentity(
            "a" * 64,
            "/dev/test",
            "sdz",
            "/sys/fake",
            "My_Passport",
            "WD",
            "PRIVATE1234",
            0,
            "1058",
            "2626",
        )
        self.assertEqual(identity.serial_suffix, "1234")
        self.assertNotIn(identity.serial, identity.display_name)

