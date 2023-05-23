__all__ = [
    "BaseError",
    "InvalidPathError",
]


class BaseError(Exception):
    pass


class InvalidPathError(BaseError):
    pass
