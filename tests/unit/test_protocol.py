import unittest

from passport_unlocker.core.constants import BLOCK_SIZE, STATUS_CDB, handy_store_read_cdb
from passport_unlocker.core.errors import (
    ProtocolSignatureError,
    ScsiTransportError,
    WrongPasswordError,
)
from passport_unlocker.core.models import SecurityState
from passport_unlocker.core.protocol import (
    WdPassportProtocol,
    handy_store_checksum,
    parse_status,
)
from passport_unlocker.core.transport import FakeScsiTransport


def status_block(state: SecurityState) -> bytes:
    data = bytearray(BLOCK_SIZE)
    data[0] = 0x45
    data[3] = state
    data[4] = 0x30
    data[6:8] = (32).to_bytes(2, "big")
    return bytes(data)


def handy_block() -> bytes:
    data = bytearray(BLOCK_SIZE)
    data[:4] = bytes.fromhex("00 01 44 57")
    data[8:12] = (2).to_bytes(4, "little")
    data[12:20] = bytes.fromhex("41 00 42 00 43 00 44 00")
    data[511] = handy_store_checksum(data)
    return bytes(data)


class ProtocolTests(unittest.TestCase):
    def test_status_parser(self) -> None:
        status = parse_status(status_block(SecurityState.LOCKED))
        self.assertIs(status.state, SecurityState.LOCKED)
        self.assertEqual(status.password_length, 32)

    def test_status_signature_is_checked(self) -> None:
        with self.assertRaises(ProtocolSignatureError):
            parse_status(bytes(BLOCK_SIZE))

    def test_unlock_bytes_and_post_write_verification(self) -> None:
        transport = FakeScsiTransport(
            [
                status_block(SecurityState.LOCKED),
                handy_block(),
                status_block(SecurityState.UNLOCKED),
            ]
        )
        after = WdPassportProtocol(transport).unlock("Test123!")
        self.assertIs(after.state, SecurityState.UNLOCKED)
        self.assertEqual(transport.commands[0], ("read", STATUS_CDB, BLOCK_SIZE))
        self.assertEqual(transport.commands[1], ("read", handy_store_read_cdb(1), BLOCK_SIZE))
        operation, cdb, payload = transport.commands[2]
        self.assertEqual(operation, "write")
        self.assertEqual(cdb, bytes.fromhex("c1 e1 00 00 00 00 00 00 28 00"))
        self.assertEqual(
            payload,
            bytes.fromhex("45 00 00 00 00 00 00 20")
            + bytes.fromhex(
                "5965eea11dfd0cd9567f5955f23489d9160943c2fec9e9802e4726ce1cdfb38b"
            ),
        )

    def test_write_success_does_not_imply_unlock(self) -> None:
        transport = FakeScsiTransport(
            [status_block(SecurityState.LOCKED), handy_block(), status_block(SecurityState.LOCKED)]
        )
        with self.assertRaises(WrongPasswordError):
            WdPassportProtocol(transport).unlock("wrong")

    def test_rejected_write_is_classified_by_followup_status(self) -> None:
        transport = FakeScsiTransport(
            [status_block(SecurityState.LOCKED), handy_block(), status_block(SecurityState.LOCKED)]
        )
        transport.write_error = ScsiTransportError("device rejected command")
        with self.assertRaises(WrongPasswordError):
            WdPassportProtocol(transport).unlock("wrong")
