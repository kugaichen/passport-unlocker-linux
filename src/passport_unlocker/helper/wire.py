import io
import json
from typing import Any, BinaryIO, TextIO

from passport_unlocker.core.errors import PassportUnlockerError

MAX_PASSWORD_BYTES = 1024


class WireProtocolError(PassportUnlockerError):
    pass


def _read_exact(stream: BinaryIO, length: int) -> bytes:
    chunks = bytearray()
    while len(chunks) < length:
        chunk = stream.read(length - len(chunks))
        if not chunk:
            raise WireProtocolError("Password input ended unexpectedly")
        chunks.extend(chunk)
    return bytes(chunks)


def read_password(stream: BinaryIO) -> bytearray:
    size = int.from_bytes(_read_exact(stream, 4), "big")
    if size <= 0 or size > MAX_PASSWORD_BYTES:
        raise WireProtocolError("Password input length is invalid")
    raw = bytearray(_read_exact(stream, size))
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        for index in range(len(raw)):
            raw[index] = 0
        raise WireProtocolError("Password input is not valid UTF-8") from exc
    return raw


def encode_password(password: str) -> bytes:
    raw = password.encode("utf-8")
    if not 0 < len(raw) <= MAX_PASSWORD_BYTES:
        raise WireProtocolError("Password input length is invalid")
    return len(raw).to_bytes(4, "big") + raw


def write_result(stream: TextIO, result: dict[str, Any]) -> None:
    json.dump(result, stream, ensure_ascii=False, separators=(",", ":"))
    stream.write("\n")
    stream.flush()


def memory_stream(password: str) -> io.BytesIO:
    return io.BytesIO(encode_password(password))

