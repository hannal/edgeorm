import re
import datetime
from functools import lru_cache
from typing import Optional, Union, TypeAlias, cast

from typing_extensions import TypedDict

import pytz

__all__ = [
    "is_aware",
    "is_naive",
    "get_default_timezone",
    "is_pytz_zone",
    "make_aware",
    "make_naive",
    "PATTERN_RELATIVE_DURATION",
    "RelativeDurationUnit",
    "parse_relative_duration",
    "format_relative_duration",
    "DateDurationUnit",
    "PATTERN_DATE_DURATION",
    "parse_date_duration",
    "format_date_duration",
]


PYTZ_BASE_CLASSES = (pytz.tzinfo.BaseTzInfo, pytz._FixedOffset)


def is_aware(value):
    if not isinstance(value, datetime.datetime):
        raise TypeError("value is required as datetime")
    return value.utcoffset() is not None


def is_naive(value):
    return value.utcoffset() is None


@lru_cache
def get_default_timezone():
    return pytz.UTC


def is_pytz_zone(tz):
    return isinstance(tz, PYTZ_BASE_CLASSES)


TimeZoneInfoType: TypeAlias = Union[
    pytz.tzinfo.StaticTzInfo, pytz.tzinfo.DstTzInfo, datetime.tzinfo
]


def make_aware(
    value: datetime.datetime,
    timezone: Optional[TimeZoneInfoType] = None,
    is_dst: Optional[bool] = None,
):
    if not isinstance(value, datetime.datetime):
        raise TypeError("value is required as datetime")

    if is_aware(value):
        return value

    timezone = timezone or get_default_timezone()

    if is_pytz_zone(timezone):
        return cast(pytz.tzinfo.DstTzInfo, timezone).localize(value, is_dst=is_dst)
    else:
        return value.replace(tzinfo=timezone)


def make_naive(value: datetime.datetime, timezone: Optional[TimeZoneInfoType] = None):
    if not isinstance(value, datetime.datetime):
        raise TypeError("value is required as datetime")

    if is_naive(value):
        return value

    timezone = timezone or get_default_timezone()
    return value.astimezone(timezone).replace(tzinfo=None)


_DATE_PATTERN = r"P((?P<year>[0-9]+)Y)?((?P<month>[0-9]+)M)?((?P<day>[0-9]+)D)?"
_TIME_PATTERN = (
    r"T((?P<hour>[0-9]+)H)?((?P<minute>[0-9]+)M)?((?P<sec>[\-]?[0-9]+)([\.](?P<msec>[0-9]+))?S)?"
)
_MONTHS_PER_YEAR = 12
_USECS_PER_HOUR = 3600000000
_USECS_PER_MINUTE = 60000000
_USECS_PER_SEC = 1000000

PATTERN_RELATIVE_DURATION = re.compile(
    "|".join(
        [
            "(PT0S)",
            rf"({_DATE_PATTERN}{_TIME_PATTERN})",
        ]
    )
)


class RelativeDurationUnit(TypedDict):
    months: int
    days: int
    microseconds: int


def parse_relative_duration(value: str) -> RelativeDurationUnit:
    matched = PATTERN_RELATIVE_DURATION.fullmatch(value)
    if not matched:
        raise ValueError("invalid RelativeDuration format")
    result = matched.groupdict()
    if not any(result.values()):
        params = {"months": 0, "days": 0, "microseconds": 0}
    else:
        converted: dict[str, int] = {_k: int(_v) if _v else 0 for _k, _v in result.items()}
        sign = -1 if converted["sec"] < 0 else 1
        params = {
            "months": converted["year"] * _MONTHS_PER_YEAR + converted["month"],
            "days": converted["day"],
            "microseconds": converted["hour"] * _USECS_PER_HOUR
            + converted["minute"] * _USECS_PER_MINUTE
            + (abs(converted["sec"]) * _USECS_PER_SEC + converted["msec"]) * sign,
        }

    return RelativeDurationUnit(
        months=params["months"] or 0,
        days=params["days"] or 0,
        microseconds=params["microseconds"] or 0,
    )


def format_relative_duration(months: int = 0, days: int = 0, microseconds: int = 0) -> str:
    if not months and not days and not microseconds:
        return "PT0S"

    date_part = format_date_duration(months=months, days=days, only_body=True)

    is_negative = microseconds < 0

    microseconds = abs(microseconds)
    units = []
    if hour := (microseconds // _USECS_PER_HOUR):
        units.append(f"{int(hour)}H")
        microseconds -= hour * _USECS_PER_HOUR
    if minute := (microseconds // _USECS_PER_MINUTE):
        units.append(f"{int(minute)}M")
        microseconds -= minute * _USECS_PER_MINUTE

    second = int(microseconds // _USECS_PER_SEC)
    microseconds = microseconds % _USECS_PER_SEC

    if is_negative:
        second = -second

    if microseconds:
        units.append(f"{second}.{microseconds}")
    else:
        units.append(str(second))

    units = "".join(units)

    return f"P{date_part}T{units}S"


class DateDurationUnit(TypedDict):
    months: int
    days: int


PATTERN_DATE_DURATION = re.compile(
    "|".join(
        [
            "(P0D)",
            rf"({_DATE_PATTERN})",
        ]
    )
)


def parse_date_duration(value: str) -> DateDurationUnit:
    matched = PATTERN_DATE_DURATION.fullmatch(value)
    if not matched:
        raise ValueError("invalid RelativeDuration format")
    result = matched.groupdict()
    if not any(result.values()):
        params = {"months": 0, "days": 0}
    else:
        converted: dict[str, int] = {_k: int(_v) if _v else 0 for _k, _v in result.items()}
        params = {
            "months": converted["year"] * _MONTHS_PER_YEAR + converted["month"],
            "days": converted["day"],
        }

    return DateDurationUnit(
        months=params["months"] or 0,
        days=params["days"] or 0,
    )


def format_date_duration(months: int = 0, days: int = 0, *, only_body=False) -> str:
    if not months and not days:
        if only_body:
            return ""
        return "P0D"

    date_parts = []
    if year := (months // 12):
        date_parts.append(f"{int(year)}Y")
    if month := (months % 12):
        date_parts.append(f"{int(month)}M")
    if days:
        date_parts.append(f"{days}D")

    date_part = "".join(date_parts)

    if not date_part:
        if only_body:
            return ""
        return "P0D"

    if only_body:
        return date_part

    return f"P{date_part}"
