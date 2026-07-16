from collections import deque
from typing import Protocol

from .errors import ScsiTransportError


class ScsiTransport(Protocol):
    def read(self, cdb: bytes, allocation_length: int) -> bytes: ...

    def write(self, cdb: bytes, payload: bytes) -> None: ...

    def close(self) -> None: ...


class FakeScsiTransport:
    def __init__(self, reads: list[bytes] | None = None) -> None:
        self.reads = deque(reads or [])
        self.commands: list[tuple[str, bytes, bytes | int]] = []
        self.write_error: Exception | None = None
        self.closed = False

    def read(self, cdb: bytes, allocation_length: int) -> bytes:
        self.commands.append(("read", cdb, allocation_length))
        if not self.reads:
            raise ScsiTransportError("No fake response configured")
        return self.reads.popleft()

    def write(self, cdb: bytes, payload: bytes) -> None:
        self.commands.append(("write", cdb, payload))
        if self.write_error is not None:
            raise self.write_error

    def close(self) -> None:
        self.closed = True

    def __enter__(self) -> "FakeScsiTransport":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

