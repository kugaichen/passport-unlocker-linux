import unittest

from passport_unlocker.core.errors import InvalidHashParametersError
from passport_unlocker.core.password import derive_password


class PasswordTests(unittest.TestCase):
    def test_golden_password_vector(self) -> None:
        result = derive_password("Test123!", 2, bytes.fromhex("41 00 42 00 43 00 44 00"))
        self.assertEqual(
            result.hex(),
            "5965eea11dfd0cd9567f5955f23489d9160943c2fec9e9802e4726ce1cdfb38b",
        )

    def test_salt_stops_at_utf16_nul(self) -> None:
        self.assertEqual(
            derive_password("x", 1, b"A\x00\x00\x00Z\x00"), derive_password("x", 1, b"A\x00")
        )

    def test_unicode_password_is_supported(self) -> None:
        self.assertEqual(len(derive_password("密碼", 1, b"A\x00")), 32)

    def test_iteration_limit_is_enforced(self) -> None:
        with self.assertRaises(InvalidHashParametersError):
            derive_password("x", 10_000_001, b"")
