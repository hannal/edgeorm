import datetime
from functools import lru_cache
from typing import Optional

import pytz

__all__ = [
    "is_aware",
    "get_default_timezone",
    "is_pytz_zone",
    "make_aware",
    "make_naive",
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


def make_aware(
    value: datetime.datetime,
    timezone: Optional[datetime.tzinfo] = None,
    is_dst: Optional[bool] = None,
):
    if not isinstance(value, datetime.datetime):
        raise TypeError("value is required as datetime")

    if is_aware(value):
        return value

    timezone = timezone or get_default_timezone()

    if is_pytz_zone(timezone):
        return timezone.localize(value, is_dst=is_dst)
    else:
        return value.replace(tzinfo=timezone)


def make_naive(value: datetime.datetime, timezone: Optional[datetime.tzinfo] = None):
    if not isinstance(value, datetime.datetime):
        raise TypeError("value is required as datetime")

    if is_naive(value):
        return value

    timezone = timezone or get_default_timezone()
    return value.astimezone(timezone).replace(tzinfo=None)
