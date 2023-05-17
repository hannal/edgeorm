from __future__ import annotations

import abc
import datetime
import re
import sys
import uuid
from decimal import Decimal as _Decimal
from typing import Generic, TypeVar, Any, Type
import json

from edgedb import DateDuration as _DateDuration
from edgedb import NamedTuple as _NamedTuple
from edgedb import Object as EdgeDBObject
from edgedb import RelativeDuration as _RelativeDuration
from pydantic.datetime_parse import parse_date, parse_datetime, parse_time
from pydantic.errors import PydanticTypeError
from pydantic.types import UUID1 as _UUID1
from pydantic.types import UUID3 as _UUID3
from pydantic.types import UUID4 as _UUID4
from pydantic.types import UUID5 as _UUID5
from pydantic.types import (
    ConstrainedBytes,
    ConstrainedDate,
    ConstrainedDecimal,
    ConstrainedFloat,
    ConstrainedInt,
    ConstrainedNumberMeta,
    ConstrainedStr,
)
from pydantic.typing import is_namedtuple
from pydantic.utils import update_not_none
from pydantic.validators import (
    bool_validator,
    list_validator,
    number_size_validator,
    set_validator,
    tuple_validator,
)

__all__ = [
    "BaseField",
    "Str",
    "Int16",
    "Int32",
    "Int64",
    "BigInt",
    "Float32",
    "Float64",
    "Decimal",
    "Date",
    "Time",
    "NaiveDateTime",
    "AwareDateTime",
    "Duration",
    "RelativeDuration",
    "DateDuration",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    "Bool",
    "Bytes",
    "Array",
    "Set",
    "Tuple",
    "NamedTuple",
    "BaseLinkField",
    "Link",
    "MultiLink",
    "Json",
    "BaseListField",
    "PolymorphicLink",
]

from nodeedge.types import BaseFilterable

T = TypeVar("T")


class BaseField(BaseFilterable):
    """Model을 정의할 때 사용하는 model field type의 base."""

    _db_link_type = None
    _db_field_type = ""
    _db_value: Any = ...
    _python_value: Any = ...

    @classmethod
    def get_validators(cls):
        for validator in cls.__get_validators__():  # type: ignore
            yield validator

    @classmethod
    def as_db_link_type(cls):
        return cls._db_link_type or cls.as_db_type()

    @classmethod
    def as_db_type(cls):
        return cls._db_field_type

    def as_db_value(self):
        if self._db_value is ...:
            return self
        return self._db_value

    @property
    def present_type(self) -> Type | Any | None:
        return None

    @property
    def to_python(self):
        if self._python_value is ...:
            return self
        return self._python_value

    def as_jsonable_value(self):
        if self._python_value is ...:
            raise ValueError(f"value is not set: {self}")
        return self.to_python
