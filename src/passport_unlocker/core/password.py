from hashlib import sha256

from .constants import MAX_HASH_ITERATIONS
from .errors import InvalidHashParametersError


def _clean_salt(salt: bytes) -> str:
    padded = salt + b"\x00\x00"
    chars: list[str] = []
    for index in range(0, len(padded) - 1, 2):
        if padded[index : index + 2] == b"\x00\x00":
            break
        chars.append(chr(padded[index]))
    return "".join(chars)


def derive_password(password: str, iteration: int, salt: bytes) -> bytes:
    if not 0 <= iteration <= MAX_HASH_ITERATIONS:
        raise InvalidHashParametersError("Hash iteration count is outside safe range")
    value = (_clean_salt(salt) + password).encode("utf-16-le")
    for _ in range(iteration):
        value = sha256(value).digest()
    return value

