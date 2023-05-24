__all__ = [
    "BaseError",
    "NotAllowedPathError",
    "InvalidPathError",
    "InvalidCompositedTypeError",
    "NotAllowedCompositionError",
]


class BaseError(Exception):
    pass


class NotAllowedPathError(BaseError):
    pass


class InvalidPathError(BaseError):
    pass


class NotAllowedCompositionError(BaseError):
    pass


class InvalidCompositedTypeError(BaseError):
    pass
