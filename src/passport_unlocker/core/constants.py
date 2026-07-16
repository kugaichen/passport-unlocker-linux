BLOCK_SIZE = 512
PASSWORD_HASH_LENGTH = 32
MAX_HASH_ITERATIONS = 10_000_000

STATUS_CDB = bytes((0xC0, 0x45, 0, 0, 0, 0, 0, 0, 0x30, 0))
STATUS_SIGNATURE = 0x45
HANDY_STORE_SIGNATURE = bytes((0x00, 0x01, 0x44, 0x57))


def handy_store_read_cdb(page: int) -> bytes:
    if not 0 <= page <= 0xFFFFFFFF:
        raise ValueError("Handy Store page is outside uint32 range")
    cdb = bytearray((0xD8, 0, 0, 0, 0, 0x01, 0, 0, 0x01, 0))
    cdb[2:6] = page.to_bytes(4, "big")
    return bytes(cdb)


def unlock_cdb(password_length: int) -> bytes:
    transfer_length = password_length + 8
    if not 0 < password_length <= 0xF7:
        raise ValueError("Password block length is outside supported range")
    return bytes((0xC1, 0xE1, 0, 0, 0, 0, 0, 0, transfer_length, 0))

