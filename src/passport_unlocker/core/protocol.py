from .constants import (
    BLOCK_SIZE,
    HANDY_STORE_SIGNATURE,
    PASSWORD_HASH_LENGTH,
    STATUS_CDB,
    STATUS_SIGNATURE,
    handy_store_read_cdb,
    unlock_cdb,
)
from .errors import (
    HandyStoreChecksumError,
    InvalidHashParametersError,
    ProtocolResponseError,
    ProtocolSignatureError,
    ScsiTransportError,
    UnlockBlockedError,
    UnsupportedDeviceError,
    WrongPasswordError,
)
from .models import EncryptionStatus, HashParameters, SecurityState
from .password import derive_password
from .transport import ScsiTransport


def handy_store_checksum(data: bytes) -> int:
    if len(data) < 510:
        raise ProtocolResponseError("Handy Store block is too short")
    return (-(sum(data[:510]) + data[0])) & 0xFF


def parse_status(data: bytes) -> EncryptionStatus:
    if len(data) < 12:
        raise ProtocolResponseError("Encryption status response is too short")
    if data[0] != STATUS_SIGNATURE:
        raise ProtocolSignatureError("Encryption status signature is invalid")
    try:
        state = SecurityState(data[3])
    except ValueError as exc:
        raise ProtocolResponseError("Encryption status value is unknown") from exc
    password_length = int.from_bytes(data[6:8], "big")
    if password_length not in (0, PASSWORD_HASH_LENGTH):
        raise ProtocolResponseError("Password block length is unsupported")
    return EncryptionStatus(state, data[4], password_length, bytes(data[8:12]))


def parse_handy_store(data: bytes) -> HashParameters:
    if len(data) != BLOCK_SIZE:
        raise ProtocolResponseError("Handy Store block must be 512 bytes")
    if handy_store_checksum(data) != data[511]:
        raise HandyStoreChecksumError("Handy Store checksum is invalid")
    if data[:4] != HANDY_STORE_SIGNATURE:
        raise ProtocolSignatureError("Handy Store signature is invalid")
    iteration = int.from_bytes(data[8:12], "little")
    if iteration <= 0:
        raise InvalidHashParametersError("Hash iteration count must be positive")
    return HashParameters(iteration, bytes(data[12:20]), bytes(data[24:226]))


def build_unlock_payload(password_hash: bytes, password_length: int) -> bytes:
    if password_length != PASSWORD_HASH_LENGTH or len(password_hash) != password_length:
        raise ProtocolResponseError("Only 32-byte password blocks are supported")
    return b"\x45\x00\x00\x00\x00\x00" + password_length.to_bytes(2, "big") + password_hash


class WdPassportProtocol:
    def __init__(self, transport: ScsiTransport) -> None:
        self._transport = transport

    def get_status(self) -> EncryptionStatus:
        return parse_status(self._transport.read(STATUS_CDB, BLOCK_SIZE))

    def read_hash_parameters(self) -> HashParameters:
        return parse_handy_store(self._transport.read(handy_store_read_cdb(1), BLOCK_SIZE))

    def unlock(self, password: str) -> EncryptionStatus:
        before = self.get_status()
        if before.state in (SecurityState.NO_LOCK, SecurityState.UNLOCKED):
            return before
        if before.state is SecurityState.LOCKED_BLOCKED:
            raise UnlockBlockedError("Drive firmware blocks further unlock attempts")
        if before.state is not SecurityState.LOCKED:
            raise UnsupportedDeviceError("Drive is not in a supported unlock state")

        parameters = self.read_hash_parameters()
        password_hash = derive_password(password, parameters.iteration, parameters.salt)
        payload = build_unlock_payload(password_hash, before.password_length)
        try:
            self._transport.write(unlock_cdb(before.password_length), payload)
        except ScsiTransportError as write_error:
            try:
                rejected_status = self.get_status()
            except ScsiTransportError as status_error:
                raise write_error from status_error
            if rejected_status.state is SecurityState.LOCKED:
                raise WrongPasswordError(
                    "Drive rejected authentication and remains locked"
                ) from write_error
            if rejected_status.state is SecurityState.LOCKED_BLOCKED:
                raise UnlockBlockedError(
                    "Drive firmware blocks further unlock attempts"
                ) from write_error
            if rejected_status.state in (SecurityState.NO_LOCK, SecurityState.UNLOCKED):
                return rejected_status
            raise write_error

        after = self.get_status()
        if after.state not in (SecurityState.NO_LOCK, SecurityState.UNLOCKED):
            if after.state is SecurityState.LOCKED_BLOCKED:
                raise UnlockBlockedError("Drive firmware blocks further unlock attempts")
            raise WrongPasswordError("Drive remained locked after authentication")
        return after
