from __future__ import annotations

from typing import Any
import json

from typing_extensions import Self
from pydantic.types import (
    ConstrainedStr,
    ConstrainedInt,
)

from nodeedge import GlobalConfiguration
from nodeedge.backends import BackendLoader
from nodeedge.backends.base import FieldTypeMap

__all__ = [
    "BaseField",
    "Str",
    "Int16",
    "Int32",
    "Int64",
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

    @classmethod
    def validate(cls, *args, **kwargs):
        for validator in cls.get_validators():
            validator(*args, **kwargs)

        return cls(*args, **kwargs)

    @classmethod
    def get_validators(cls):
        for validator in cls.__get_validators__():
            yield validator

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

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
        return json.dumps(self.as_python_value())


class Str(ConstrainedStr, BaseField):
    @classmethod
    def validate(cls, value: str) -> Self:
        result = cls(super().validate(value))
        result._python_value = str(result)
        return result


class Int16(ConstrainedInt, BaseField):
    ge = -32_768
    le = 32_767

    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: int) -> Self:
        result = cls(value)
        result._python_value = int(result)
        return result


class Int32(ConstrainedInt, BaseField):
    ge = -2_147_483_648
    le = 2_147_483_647

    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: int) -> Self:
        result: Int32 = cls(value)
        result._python_value = int(result)
        return result


class Int64(ConstrainedInt, BaseField):
    ge = -9_223_372_036_854_775_808
    le = 9_223_372_036_854_775_807

    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: int) -> Self:
        result: Int64 = cls(value)
        result._python_value = int(result)
        return result
