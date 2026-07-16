class PassportUnlockerError(Exception):
    """Base class for expected application failures."""


class UnsupportedDeviceError(PassportUnlockerError):
    pass


class DeviceNotFoundError(PassportUnlockerError):
    pass


class DeviceIdentityChangedError(PassportUnlockerError):
    pass


class PermissionDeniedError(PassportUnlockerError):
    pass


class DeviceDisconnectedError(PassportUnlockerError):
    pass


class ProtocolSignatureError(PassportUnlockerError):
    pass


class ProtocolResponseError(PassportUnlockerError):
    pass


class HandyStoreChecksumError(PassportUnlockerError):
    pass


class InvalidHashParametersError(PassportUnlockerError):
    pass


class WrongPasswordError(PassportUnlockerError):
    pass


class UnlockBlockedError(PassportUnlockerError):
    pass


class ScsiTransportError(PassportUnlockerError):
    pass


class RescanError(PassportUnlockerError):
    pass


class RescanTimeoutError(PassportUnlockerError):
    pass

