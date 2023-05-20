from __future__ import annotations

import datetime
import json
import re
from typing import (
    Any,
    Union,
    Optional,
    TypeVar,
    cast,
)
from decimal import Decimal as _Decimal

from edgedb import DateDuration as _DateDuration
from edgedb import RelativeDuration as _RelativeDuration
from typing_extensions import Self, TypeAlias
from pydantic.typing import is_namedtuple
from pydantic.errors import PydanticTypeError
from pydantic.datetime_parse import StrBytesIntFloat, parse_date, parse_datetime, parse_time
from pydantic.types import UUID1 as _UUID1
from pydantic.types import UUID3 as _UUID3
from pydantic.types import UUID4 as _UUID4
from pydantic.types import UUID5 as _UUID5
from pydantic.types import (
    ConstrainedStr,
    ConstrainedInt,
    ConstrainedFloat,
    ConstrainedDecimal,
    ConstrainedDate,
    ConstrainedNumberMeta,
    ConstrainedBytes,
)
from pydantic.utils import update_not_none
from pydantic.validators import (
    bool_validator,
    list_validator,
    number_size_validator,
    set_validator,
    tuple_validator,
)

from nodeedge.utils.datetime import (
    is_aware,
    make_naive,
    is_naive,
    make_aware,
    parse_relative_duration,
    format_relative_duration,
    parse_date_duration,
    format_date_duration,
)

from .base_fields import (
    BaseField,
    BaseListField,
    PythonValueFieldMixin,
    BaseUUIDField,
)


__all__ = [
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
    "Duration",
    "RelativeDuration",
    "DateDuration",
    "Json",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    "Bytes",
    "Array",
    "Set",
    "Tuple",
    "NamedTuple",
]


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
        result = cls(value)
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
        result = cls(value)
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
        result = cls(super().validate(cast(_Decimal, value)))
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


_IsoFormattableType: TypeAlias = Union[datetime.date, datetime.time, datetime.datetime]


class _IsoFormatField(PythonValueFieldMixin[_IsoFormattableType]):
    def as_jsonable_value(self):
        return cast(_IsoFormattableType, self.as_python_value()).isoformat()


class Date(ConstrainedDate, _IsoFormatField, BaseField):
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


class Time(datetime.time, _IsoFormatField, BaseField, metaclass=ConstrainedNumberMeta):
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


class NaiveDateTime(datetime.datetime, _IsoFormatField, BaseField, metaclass=ConstrainedNumberMeta):
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


class AwareDateTime(datetime.datetime, _IsoFormatField, BaseField, metaclass=ConstrainedNumberMeta):
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


_SECS_PER_MINUTE = 60
_SECS_PER_HOUR = 3600


class Duration(datetime.timedelta, BaseField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: datetime.timedelta) -> Self:
        if not isinstance(value, datetime.timedelta):
            raise ValueError("invalid timedelta")

        result = cls(days=value.days, seconds=value.seconds, microseconds=value.microseconds)
        result._python_value = value
        return result

    def as_jsonable_value(self):
        return self.format_duration()

    def format_duration(self) -> str:
        value = self.as_python_value()
        total_seconds = value.total_seconds()

        time_parts = []
        if hour := (total_seconds // _SECS_PER_HOUR):
            time_parts.append(f"{int(hour)} hours")
            total_seconds -= hour * _SECS_PER_HOUR
        if minute := (total_seconds // _SECS_PER_MINUTE):
            time_parts.append(f"{int(minute)} minutes")
            total_seconds -= minute * _SECS_PER_MINUTE

        if total_seconds:
            time_parts.append(f"{int(total_seconds)} seconds")

        if value.microseconds:
            time_parts.append(f"{value.microseconds} microseconds")

        return " ".join(time_parts)


class RelativeDuration(ConstrainedStr, BaseField):
    _edgedb_value: _RelativeDuration
    months: int
    days: int
    microseconds: int

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> Self:
        result = cls(value)
        parsed = parse_relative_duration(value)
        result.months = parsed["months"] or 0
        result.days = parsed["days"] or 0
        result.microseconds = parsed["microseconds"] or 0
        result._db_value = _RelativeDuration(**parsed)
        result._python_value = value
        return result

    def as_jsonable_value(self):
        return format_relative_duration(self.months, self.days, self.microseconds)


class DateDuration(ConstrainedStr, BaseField):
    _edgedb_value: _DateDuration
    months: int
    days: int

    @classmethod
    def validate(cls, value: str) -> Self:
        result = cls(value)
        parsed = parse_date_duration(value)
        result.months = parsed["months"] or 0
        result.days = parsed["days"] or 0
        result._db_value = _DateDuration(**parsed)
        result._python_value = value
        return result

    def as_jsonable_value(self):
        return format_date_duration(self.months, self.days, only_body=False)


class Json(ConstrainedStr, BaseField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: str) -> "Json":
        result = cls(value)
        result._db_value = json.loads(value)
        result._python_value = value
        return result

    def as_jsonable_value(self):
        return self.as_db_value()


class UUID1(_UUID1, BaseUUIDField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class UUID3(_UUID3, BaseUUIDField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class UUID4(_UUID4, BaseUUIDField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class UUID5(_UUID5, BaseUUIDField):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate


class Bytes(ConstrainedBytes, BaseField):
    @classmethod
    def __get_validators__(cls):
        for validator in super().__get_validators__():
            yield validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        result = cls(value)
        return result

    def as_jsonable_value(self):
        return self.decode()


Listable_T = TypeVar("Listable_T")


class Array(BaseListField[Listable_T], BaseField):
    _data: list[Listable_T]

    @classmethod
    def __get_validators__(cls):
        yield list_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, Array):
            target = value.data
        else:
            target = value

        result = cls(list(target))
        result._python_value = result.data
        return result


class Set(BaseListField[Listable_T], BaseField):
    @classmethod
    def __get_validators__(cls):
        yield set_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, Set):
            target = value.data
        else:
            target = value

        result = cls(list(target))
        result._python_value = set(target)
        result._db_value = result.data
        return result


class Tuple(BaseListField[Listable_T], BaseField):
    @classmethod
    def __get_validators__(cls):
        yield tuple_validator
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, Tuple):
            target = value.data
        else:
            target = value

        result = cls(tuple(target))
        result._python_value = result.data
        return result


class NamedTuple(BaseListField[Listable_T], BaseField):
    class NamedTupleError(PydanticTypeError):
        msg_template = "value is not a valid namedtuple"

    @classmethod
    def __get_validators__(cls):
        yield cls.is_namedtuple
        yield cls.validate

    @classmethod
    def is_namedtuple(cls, value: Any):
        if is_namedtuple(type(value)):
            return value
        raise cls.NamedTupleError

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, NamedTuple):
            target = value.data
        else:
            target = value

        result = cls(target)
        result._python_value = result.data
        result._db_value = tuple(result.data)
        return result
