from __future__ import annotations

import re
from typing import Any, Union, Optional
import json
from decimal import Decimal as _Decimal
import datetime

from typing_extensions import Self
import pydantic
from pydantic.datetime_parse import StrBytesIntFloat, parse_date, parse_datetime, parse_time
from pydantic.types import (
    ConstrainedStr,
    ConstrainedInt,
    ConstrainedFloat,
    ConstrainedDecimal,
    ConstrainedDate,
    ConstrainedNumberMeta,
)
from pydantic.utils import update_not_none
from pydantic.validators import (
    bool_validator,
    list_validator,
    number_size_validator,
    set_validator,
    tuple_validator,
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
    "BigInt",
    "Float32",
    "Float64",
    "Decimal",
    "Bool",
    "Date",
    "Time",
    "NaiveDateTime",
    "AwareDateTime",
]

from nodeedge.types import BaseFilterable
from nodeedge.utils.datetime import is_aware, make_naive, is_naive, make_aware

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


class BigInt(ConstrainedStr, BaseField):
    regex = re.compile(r"((?P<value>[0-9]+)(e\+(?P<exponent>[0-9]+))?)n")

    @classmethod
    def validate(cls, value: str) -> Self:
        matched = cls.regex.fullmatch(value)
        if not matched:
            raise ValueError("invalid BigInt format")

        matched_dict = matched.groupdict()
        converted: dict[str, int]
        if not any(matched_dict.values()):
            converted = {"value": 0, "exponent": 0}
        else:
            converted = {_k: int(_v) if _v else 0 for _k, _v in matched_dict.items()}

        result = cls(super().validate(value))
        result._python_value = int(float(f"{converted['value']}e{converted['exponent']}"))
        return result

    def as_jsonable_value(self):
        return json.dumps(self)


class Float32(ConstrainedFloat, BaseField):
    ge = -3.4e38
    le = 3.4e38

    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: float) -> Self:
        result = cls(value)
        result._python_value = float(result)
        return result


class Float64(ConstrainedFloat, BaseField):
    ge = -1.7e308
    le = 1.7e308

    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: float) -> Self:
        result = cls(value)
        result._python_value = float(result)
        return result


class Decimal(ConstrainedDecimal, BaseField):
    @classmethod
    def validate(cls, value: _Decimal | int | str) -> Self:
        result = cls(super().validate(value))
        result._python_value = result
        return result

    def as_jsonable_value(self):
        return str(self.as_python_value())


class Bool(int, BaseField):
    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        field_schema.update(type="boolean")

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        result = cls(bool_validator(value))
        result._python_value = True if result else False
        return result


class Date(ConstrainedDate, BaseField):
    @classmethod
    def __get_validators__(cls):
        yield parse_date
        yield number_size_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[datetime.date, StrBytesIntFloat]) -> Self:
        if not isinstance(value, datetime.date):
            value = parse_date(value)
        result = cls(value.year, value.month, value.day)
        result._python_value = value
        return result

    @classmethod
    def today(cls) -> Self:
        return cls.validate(datetime.date.today())

    def as_jsonable_value(self):
        return self.as_python_value().isoformat()


class Time(datetime.time, BaseField, metaclass=ConstrainedNumberMeta):
    gt: Optional[datetime.time] = None
    ge: Optional[datetime.time] = None
    lt: Optional[datetime.time] = None
    le: Optional[datetime.time] = None

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            exclusiveMinimum=cls.gt,
            exclusiveMaximum=cls.lt,
            minimum=cls.ge,
            maximum=cls.le,
        )

    @classmethod
    def __get_validators__(cls):
        yield parse_time
        yield number_size_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[datetime.time, StrBytesIntFloat]) -> Self:
        if not isinstance(value, datetime.time):
            value = parse_time(value)
        result = cls(
            value.hour, value.minute, value.second, value.microsecond, value.tzinfo, fold=value.fold
        )
        result._python_value = value
        return result

    @classmethod
    def now(cls):
        return cls.validate(datetime.datetime.utcnow().time())

    def as_jsonable_value(self):
        return self.as_python_value().isoformat()


class NaiveDateTime(datetime.datetime, BaseField, metaclass=ConstrainedNumberMeta):
    gt: Optional[datetime.datetime] = None
    ge: Optional[datetime.datetime] = None
    lt: Optional[datetime.datetime] = None
    le: Optional[datetime.datetime] = None

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            exclusiveMinimum=cls.gt,
            exclusiveMaximum=cls.lt,
            minimum=cls.ge,
            maximum=cls.le,
        )

    @classmethod
    def __get_validators__(cls):
        yield parse_datetime
        yield number_size_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[datetime.datetime, StrBytesIntFloat]) -> Self:
        if not isinstance(value, datetime.datetime):
            value = parse_datetime(value)
        if is_aware(value):
            raise ValueError("datetime is off-set awarded")
        result = cls(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            value.tzinfo,
            fold=value.fold,
        )
        result._python_value = value
        return result

    @classmethod
    def now(cls, tz: Optional[datetime.tzinfo] = None) -> Self:
        return cls.validate(make_naive(datetime.datetime.now(tz)))

    def as_jsonable_value(self):
        return self.as_python_value().isoformat()


class AwareDateTime(datetime.datetime, BaseField, metaclass=ConstrainedNumberMeta):
    gt: Optional[datetime.datetime] = None
    ge: Optional[datetime.datetime] = None
    lt: Optional[datetime.datetime] = None
    le: Optional[datetime.datetime] = None

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]) -> None:
        update_not_none(
            field_schema,
            exclusiveMinimum=cls.gt,
            exclusiveMaximum=cls.lt,
            minimum=cls.ge,
            maximum=cls.le,
        )

    @classmethod
    def __get_validators__(cls):
        yield parse_datetime
        yield number_size_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[datetime.datetime, StrBytesIntFloat]) -> Self:
        if not isinstance(value, datetime.datetime):
            value = parse_datetime(value)
        if is_naive(value):
            raise ValueError("datetime is not off-set awarded")
        result = cls(
            value.year,
            value.month,
            value.day,
            value.hour,
            value.minute,
            value.second,
            value.microsecond,
            value.tzinfo,
            fold=value.fold,
        )
        result._python_value = value
        return result

    @classmethod
    def now(cls, tz: Optional[datetime.tzinfo] = None) -> Self:
        return cls.validate(make_aware(datetime.datetime.now(tz)))

    def as_jsonable_value(self):
        return self.as_python_value().isoformat()
