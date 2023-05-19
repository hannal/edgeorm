from .types import ValueClass


class GlobalConfiguration(metaclass=ValueClass):
    BACKEND = "nodeedge.backends.edgedb"

    @classmethod
    def is_edgedb_backend(cls):
        return "edgedb" in cls.BACKEND
