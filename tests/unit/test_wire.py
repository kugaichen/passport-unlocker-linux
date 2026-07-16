import io
import json
import unittest

from passport_unlocker.helper.wire import (
    WireProtocolError,
    encode_password,
    read_password,
    write_result,
)


class WireTests(unittest.TestCase):
    def test_round_trip(self) -> None:
        encoded = encode_password("正确-password")
        self.assertEqual(read_password(io.BytesIO(encoded)).decode(), "正确-password")

    def test_truncated_input_is_rejected(self) -> None:
        with self.assertRaises(WireProtocolError):
            read_password(io.BytesIO(b"\x00\x00\x00\x05abc"))

    def test_oversized_input_is_rejected(self) -> None:
        with self.assertRaises(WireProtocolError):
            read_password(io.BytesIO((1025).to_bytes(4, "big")))

    def test_json_is_one_line(self) -> None:
        stream = io.StringIO()
        write_result(stream, {"ok": True})
        self.assertEqual(json.loads(stream.getvalue()), {"ok": True})
        self.assertEqual(stream.getvalue().count("\n"), 1)
