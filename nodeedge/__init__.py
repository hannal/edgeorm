from .types import ValueClass, UndefinedType
from .constants import Undefined


__all__ = ["Undefined", "ValueClass", "UndefinedType", "GlobalConfiguration"]


class GlobalConfiguration(metaclass=ValueClass):
    BACKEND = "nodeedge.backends.edgedb"

    @classmethod
    def is_edgedb_backend(cls):
        return "edgedb" in cls.BACKEND
