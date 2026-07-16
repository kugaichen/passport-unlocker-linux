from __future__ import annotations

import ctypes
import os

from .constants import BLOCK_SIZE, STATUS_CDB, handy_store_read_cdb, unlock_cdb
from .errors import ScsiTransportError

SG_IO = 0x2285
SG_DXFER_TO_DEV = -2
SG_DXFER_FROM_DEV = -3
SG_INFO_OK_MASK = 0x1
SG_INFO_OK = 0x0


class _SgIoHeader(ctypes.Structure):
    _fields_ = [
        ("interface_id", ctypes.c_int),
        ("dxfer_direction", ctypes.c_int),
        ("cmd_len", ctypes.c_ubyte),
        ("mx_sb_len", ctypes.c_ubyte),
        ("iovec_count", ctypes.c_ushort),
        ("dxfer_len", ctypes.c_uint),
        ("dxferp", ctypes.c_void_p),
        ("cmdp", ctypes.c_void_p),
        ("sbp", ctypes.c_void_p),
        ("timeout", ctypes.c_uint),
        ("flags", ctypes.c_uint),
        ("pack_id", ctypes.c_int),
        ("usr_ptr", ctypes.c_void_p),
        ("status", ctypes.c_ubyte),
        ("masked_status", ctypes.c_ubyte),
        ("msg_status", ctypes.c_ubyte),
        ("sb_len_wr", ctypes.c_ubyte),
        ("host_status", ctypes.c_ushort),
        ("driver_status", ctypes.c_ushort),
        ("resid", ctypes.c_int),
        ("duration", ctypes.c_uint),
        ("info", ctypes.c_uint),
    ]


class LinuxSgIoTransport:
    """Minimal SG_IO transport restricted to the three v0.1 protocol requests."""

    def __init__(self, device_node: str, timeout_ms: int = 20_000) -> None:
        if os.name != "posix":
            raise ScsiTransportError("SG_IO transport is available only on Linux")
        flags = os.O_RDWR | getattr(os, "O_CLOEXEC", 0)
        try:
            self._fd = os.open(device_node, flags)
        except OSError as exc:
            raise ScsiTransportError("Unable to open raw block device") from exc
        self._timeout_ms = timeout_ms

    @staticmethod
    def _allowed_read(cdb: bytes, length: int) -> bool:
        return length == BLOCK_SIZE and cdb in (STATUS_CDB, handy_store_read_cdb(1))

    @staticmethod
    def _allowed_write(cdb: bytes, payload: bytes) -> bool:
        return (
            cdb == unlock_cdb(32)
            and len(payload) == 40
            and payload[:8] == bytes.fromhex("45 00 00 00 00 00 00 20")
        )

    def _ioctl(self, cdb: bytes, data: ctypes.Array[ctypes.c_char], direction: int) -> None:
        command = ctypes.create_string_buffer(cdb)
        sense = ctypes.create_string_buffer(64)
        header = _SgIoHeader()
        header.interface_id = ord("S")
        header.dxfer_direction = direction
        header.cmd_len = len(cdb)
        header.mx_sb_len = len(sense)
        header.dxfer_len = len(data)
        header.dxferp = ctypes.addressof(data)
        header.cmdp = ctypes.addressof(command)
        header.sbp = ctypes.addressof(sense)
        header.timeout = self._timeout_ms
        libc = ctypes.CDLL(None, use_errno=True)
        if libc.ioctl(self._fd, SG_IO, ctypes.byref(header)) < 0:
            error_number = ctypes.get_errno()
            raise ScsiTransportError(f"SG_IO ioctl failed with errno {error_number}")
        if (
            header.status
            or header.host_status
            or header.driver_status
            or (header.info & SG_INFO_OK_MASK) != SG_INFO_OK
        ):
            raise ScsiTransportError("SCSI request was rejected by the device")

    def read(self, cdb: bytes, allocation_length: int) -> bytes:
        if not self._allowed_read(cdb, allocation_length):
            raise ScsiTransportError("Read CDB is outside the fixed protocol allowlist")
        data = ctypes.create_string_buffer(allocation_length)
        self._ioctl(cdb, data, SG_DXFER_FROM_DEV)
        return data.raw

    def write(self, cdb: bytes, payload: bytes) -> None:
        if not self._allowed_write(cdb, payload):
            raise ScsiTransportError("Write CDB is outside the fixed protocol allowlist")
        data = ctypes.create_string_buffer(payload, len(payload))
        self._ioctl(cdb, data, SG_DXFER_TO_DEV)

    def close(self) -> None:
        fd = getattr(self, "_fd", -1)
        if fd >= 0:
            os.close(fd)
            self._fd = -1

    def __enter__(self) -> LinuxSgIoTransport:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def __del__(self) -> None:
        self.close()
