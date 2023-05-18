from __future__ import annotations

from typing import Any, Union
import json

from typing_extensions import Self
from pydantic.types import (
    ConstrainedStr,
)

from nodeedge import GlobalConfiguration
from nodeedge.backends import BackendLoader
from nodeedge.backends.base import FieldTypeMap

__all__ = [
    "BaseField",
    "Str",
]

from nodeedge.types import BaseFilterable


_backend = BackendLoader(GlobalConfiguration.BACKEND)
_field_type_map = _backend.field_type_map


class BaseField(BaseFilterable):
    """Model을 정의할 때 사용하는 model field type의 base."""

    _backend: str = _backend
    _field_type_map: FieldTypeMap = _field_type_map

    _db_link_type = None
    _db_field_type = None
    _db_value: Any = ...
    _python_value: Any = ...

    def __get__(self, instance, owner: Union[Any, None] = None):
        if not owner:
            raise TypeError("owner is not set")

        if instance is None:
            return self
        return instance

    @classmethod
    def get_validators(cls):
        for validator in cls.__get_validators__():  # type: ignore
            yield validator

    @classmethod
    def as_db_link_type(cls):
        return cls._db_link_type or cls.as_db_type()

    @classmethod
    def as_db_type(cls):
        return cls._db_field_type or getattr(cls._field_type_map, cls.__name__)

    def as_db_value(self):
        if self._db_value is ...:
            return self
        return self._db_value

    def as_python_value(self):
        if self._python_value is ...:
            return self
        return self._python_value

    def as_jsonable_value(self):
        if self._python_value is ...:
            raise ValueError(f"value is not set: {self}")
        return self.as_python_value()


class Str(ConstrainedStr, BaseField):  # type: ignore
    @classmethod
    def validate(cls, value: str) -> Self:
        result: Str = cls(super().validate(value))
        result._python_value = str(result)
        return result

    def as_jsonable_value(self):
        return json.dumps(self.as_python_value())
