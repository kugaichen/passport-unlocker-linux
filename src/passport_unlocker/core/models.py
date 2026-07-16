from dataclasses import dataclass
from enum import Enum, IntEnum


class SecurityState(IntEnum):
    NO_LOCK = 0x00
    LOCKED = 0x01
    UNLOCKED = 0x02
    LOCKED_BLOCKED = 0x06
    NO_KEYS = 0x07


class OperationState(str, Enum):
    IDLE = "idle"
    AUTHORIZING = "authorizing"
    CHECKING = "checking"
    UNLOCKING = "unlocking"
    RESCANNING = "rescanning"
    WAITING_FOR_DEVICE = "waiting_for_device"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class EncryptionStatus:
    state: SecurityState
    cipher_id: int
    password_length: int
    key_reset_enabler: bytes


@dataclass(frozen=True)
class HashParameters:
    iteration: int
    salt: bytes
    hint: bytes
