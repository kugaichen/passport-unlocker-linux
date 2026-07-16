import unittest

from passport_unlocker.core.constants import (
    BLOCK_SIZE,
    STATUS_CDB,
    handy_store_read_cdb,
    unlock_cdb,
)
from passport_unlocker.core.linux_sg_io import LinuxSgIoTransport


class AllowlistTests(unittest.TestCase):
    def test_only_fixed_reads_are_allowed(self) -> None:
        self.assertTrue(LinuxSgIoTransport._allowed_read(STATUS_CDB, BLOCK_SIZE))
        self.assertTrue(LinuxSgIoTransport._allowed_read(handy_store_read_cdb(1), BLOCK_SIZE))
        self.assertFalse(LinuxSgIoTransport._allowed_read(b"\x00", BLOCK_SIZE))

    def test_only_unlock_write_is_allowed(self) -> None:
        payload = bytes.fromhex("45 00 00 00 00 00 00 20") + bytes(32)
        self.assertTrue(LinuxSgIoTransport._allowed_write(unlock_cdb(32), payload))
        self.assertFalse(LinuxSgIoTransport._allowed_write(bytes.fromhex("c1 e3"), payload))
