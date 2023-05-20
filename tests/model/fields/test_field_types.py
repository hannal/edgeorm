import datetime
import json
import uuid
from typing import Type, Any
from decimal import Decimal
from collections import namedtuple

import pytest
from pydantic import ValidationError
from pydantic.validators import BOOL_TRUE, BOOL_FALSE
from edgedb import DateDuration as _DateDuration
from edgedb import RelativeDuration as _RelativeDuration

from nodeedge.model import fields, Model
from nodeedge.utils.datetime import make_aware, RelativeDurationUnit, DateDurationUnit
from _testing.decorators import skip_if_not_edgedb


def test_str():
    class SampleModel(Model):
        field: fields.Str

    value = "hello world"
    model = SampleModel(field=value)

    assert model.field == value
    assert model.field.as_db_type() == "str"
    assert model.field.as_db_value() == value
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == f'"{value}"'


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value", "expected_db_type"],
    [
        [fields.Int16, 1, "int16"],
        [fields.Int32, 1, "int32"],
        [fields.Int64, 1, "int64"],
    ],
)
def test_valid_int(
    field_type: Type[fields.BaseField],
    value: int,
    expected_db_type: str,
):
    class SampleModel(Model):
        field: field_type

    model = SampleModel(field=value)

    assert model.field == value
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == value
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == f"{value}"


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value"],
    [
        [fields.Int16, fields.Int16.le + 1],
        [fields.Int16, fields.Int16.ge - 1],
        [fields.Int32, fields.Int32.le + 1],
        [fields.Int32, fields.Int32.ge - 1],
        [fields.Int64, fields.Int64.le + 1],
        [fields.Int64, fields.Int64.ge - 1],
        [fields.Int16, "invalid"],
        [fields.Int32, "invalid"],
        [fields.Int64, "invalid"],
    ],
)
def test_invalid_int(field_type: Type[fields.BaseField], value: Any):
    class SampleModel(Model):
        field: field_type

    with pytest.raises(ValidationError):
        SampleModel(field=value)


@skip_if_not_edgedb
def test_bigint():
    class SampleModel(Model):
        field: fields.BigInt

    expected_db_type = "bigint"
    expected_python_value = int(1e100)
    value = "1e+100n"
    model = SampleModel(field=value)
    assert model.field == value
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == value
    assert model.field.as_python_value() == expected_python_value
    assert model.field.as_jsonable_value() == f'"{value}"'


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value", "expected_db_type"],
    [
        [fields.Float32, 1.0, "float32"],
        [fields.Float64, 1.0, "float64"],
    ],
)
def test_valid_float(field_type: Type[fields.BaseField], value, expected_db_type):
    class SampleModel(Model):
        field: field_type

    model = SampleModel(field=value)
    assert model.field == value
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == value
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == f"{value}"


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value"],
    [
        [fields.Float32, fields.Float32.le * 10],
        [fields.Float32, fields.Float32.ge * 10],
        [fields.Float64, fields.Float64.le * 10],
        [fields.Float64, fields.Float64.ge * 10],
        [fields.Float32, "invalid"],
        [fields.Float64, "invalid"],
    ],
)
def test_invalid_float(field_type: Type[fields.BaseField], value: Any):
    class SampleModel(Model):
        field: field_type

    with pytest.raises(ValidationError):
        SampleModel(field=value)


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["value", "expected", "expected_python_value", "expected_json_value"],
    [
        ["1.7e30", Decimal("1.7e30"), Decimal("1.7e30"), "1.7E+30"],
        [1_000_000_000.456, Decimal("1000000000.456"), Decimal("1000000000.456"), "1000000000.456"],
        [1_000_000_000, Decimal("1000000000"), Decimal("1000000000"), "1000000000"],
        [Decimal("1.7e30"), Decimal("1.7e30"), Decimal("1.7e30"), "1.7E+30"],
    ],
)
def test_decimal(value, expected, expected_python_value, expected_json_value):
    class SampleModel(Model):
        field: fields.Decimal

    expected_db_type = "decimal"
    model = SampleModel(field=value)

    assert model.field == expected
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == expected_python_value
    assert model.field.as_python_value() == expected_python_value
    assert model.field.as_jsonable_value() == expected_json_value


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["value", "expected"],
    [
        *[[_v, True] for _v in BOOL_TRUE],
        *[[_v, False] for _v in BOOL_FALSE],
    ],
)
def test_bool(value, expected):
    class SampleModel(Model):
        field: fields.Bool

    expected_db_type = "bool"
    model = SampleModel(field=value)

    assert model.field == expected
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == expected
    assert model.field.as_python_value() == expected
    assert model.field.as_jsonable_value() == str(expected).lower()


_today = datetime.date.today()
_naive_now = datetime.datetime.now()
_aware_now = make_aware(datetime.datetime.utcnow())


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value", "expected_type", "expected_db_type", "expected_json_value"],
    [
        [fields.Date, _today.isoformat(), datetime.date, "cal::local_date", _today.isoformat()],
        [fields.Date, _today.isoformat(), datetime.date, "cal::local_date", _today.isoformat()],
        [
            fields.Time,
            _naive_now.time().isoformat(),
            datetime.time,
            "cal::local_time",
            _naive_now.time().isoformat(),
        ],
        [
            fields.Time,
            _naive_now.time(),
            datetime.time,
            "cal::local_time",
            _naive_now.time().isoformat(),
        ],
        [
            fields.NaiveDateTime,
            _naive_now.isoformat(),
            datetime.datetime,
            "cal::local_datetime",
            _naive_now.isoformat(),
        ],
        [
            fields.NaiveDateTime,
            _naive_now,
            datetime.datetime,
            "cal::local_datetime",
            _naive_now.isoformat(),
        ],
        [
            fields.AwareDateTime,
            _aware_now.isoformat(),
            datetime.datetime,
            "datetime",
            _aware_now.isoformat(),
        ],
        [
            fields.AwareDateTime,
            _aware_now,
            datetime.datetime,
            "datetime",
            _aware_now.isoformat(),
        ],
    ],
)
def test_datetime(
    field_type: Type[fields.BaseField],
    value,
    expected_type,
    expected_db_type,
    expected_json_value,
):
    class SampleModel(Model):
        field: field_type

    model = SampleModel(field=value)

    assert isinstance(model.field.as_python_value(), expected_type)
    expected_db_value = model.field.as_python_value()
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == expected_db_value
    assert model.field.as_python_value() == expected_db_value
    assert model.field.as_jsonable_value() == expected_json_value


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["value", "expected_json_value"],
    [
        [datetime.timedelta(days=1), "24 hours"],
        [datetime.timedelta(days=3, hours=10, seconds=5), "82 hours 5 seconds"],
    ],
)
def test_duration(value, expected_json_value):
    class SampleModel(Model):
        field: fields.Duration

    expected_type = datetime.timedelta
    expected_db_type = "duration"

    model = SampleModel(field=value)

    assert isinstance(model.field.as_python_value(), expected_type)
    expected_db_value = model.field.as_python_value()
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == expected_db_value
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == expected_json_value


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["value", "expected_units"],
    [
        ["PT0S", {"months": 0, "days": 0, "microseconds": 0}],
        ["P1Y3M34DT0S", {"months": 15, "days": 34, "microseconds": 0}],
        ["PT-35S", {"months": 0, "days": 0, "microseconds": -35 * 1_000_000}],
        ["PT35.431000S", {"months": 0, "days": 0, "microseconds": 35 * 1_000_000 + 431000}],
    ],
)
def test_relative_duration(value, expected_units: RelativeDurationUnit):
    class SampleModel(Model):
        field: fields.RelativeDuration

    expected_db_type = "cal::relative_duration"

    model = SampleModel(field=value)

    assert isinstance(model.field.as_python_value(), str)
    assert model.field.as_db_type() == expected_db_type
    assert isinstance(model.field.as_db_value(), _RelativeDuration)
    assert model.field.months == expected_units["months"]
    assert model.field.days == expected_units["days"]
    assert model.field.microseconds == expected_units["microseconds"]
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == value


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["value", "expected_units"],
    [
        ["P0D", {"months": 0, "days": 0}],
        ["P1Y3M34D", {"months": 15, "days": 34}],
    ],
)
def test_date_duration(value, expected_units: DateDurationUnit):
    class SampleModel(Model):
        field: fields.DateDuration

    expected_db_type = "cal::date_duration"

    model = SampleModel(field=value)

    assert isinstance(model.field.as_python_value(), str)
    assert model.field.as_db_type() == expected_db_type
    assert isinstance(model.field.as_db_value(), _DateDuration)
    assert model.field.months == expected_units["months"]
    assert model.field.days == expected_units["days"]
    assert model.field.as_python_value() == value
    assert model.field.as_jsonable_value() == value


@skip_if_not_edgedb
def test_json():
    class SampleModel(Model):
        field: fields.Json

    expected_db_type = "json"
    jsonable_value = {"hello": "world"}
    value = json.dumps(jsonable_value)

    model = SampleModel(field=value)
    assert model.field.as_db_type() == expected_db_type
    assert isinstance(model.field, str)
    assert isinstance(model.field.as_python_value(), str)
    assert model.field.as_db_value() == jsonable_value
    assert model.field.as_jsonable_value() == jsonable_value


@skip_if_not_edgedb
@pytest.mark.parametrize(
    ["field_type", "value", "expected_db_type"],
    [
        [fields.UUID1, uuid.uuid1(clock_seq=123), "uuid"],
        [fields.UUID3, uuid.uuid3(uuid.NAMESPACE_DNS, "nodeedge"), "uuid"],
        [fields.UUID4, uuid.uuid4(), "uuid"],
        [fields.UUID5, uuid.uuid5(uuid.NAMESPACE_DNS, "nodeedge"), "uuid"],
    ],
)
def test_uuids(field_type: Type[fields.BaseField], value, expected_db_type):
    class SampleModel(Model):
        field: field_type

    model = SampleModel(field=value)
    assert model.field == value
    assert model.field.as_db_type() == expected_db_type
    assert model.field.as_db_value() == str(value)


@skip_if_not_edgedb
def test_bytes():
    class SampleModel(Model):
        field: fields.Bytes

    value = "asdf"
    model = SampleModel(field=value)
    assert model.field.as_db_type() == "bytes"
    assert isinstance(model.field, bytes)
    assert isinstance(model.field.as_python_value(), bytes)
    assert isinstance(model.field.as_db_value(), bytes)


@skip_if_not_edgedb
def test_array():
    class SampleModel(Model):
        field: fields.Array[str]

    value = ["asdf"]
    model = SampleModel(field=value)

    assert model.field.as_db_type() == "array"
    assert isinstance(model.field.as_db_value(), list)
    assert model.field.data == value
    assert model.field.as_db_value() == value
    assert model.field.as_python_value() == value


@skip_if_not_edgedb
def test_set():
    class SampleModel(Model):
        field: fields.Set[str]

    value = {"asdf"}
    model = SampleModel(field=value)

    assert model.field.as_db_type() == "set"
    assert isinstance(model.field.as_db_value(), list)
    assert model.field.data == list(value)
    assert model.field.as_db_value() == list(value)
    assert model.field.as_python_value() == set(value)


@skip_if_not_edgedb
def test_tuple():
    class SampleModel(Model):
        field: fields.Tuple[str]

    value = ("asdf",)
    model = SampleModel(field=value)
    assert model.field.as_db_type() == "tuple"
    assert isinstance(model.field.as_db_value(), list)
    assert model.field.data == value
    assert model.field.as_db_value() == list(value)
    assert model.field.as_python_value() == tuple(value)


@skip_if_not_edgedb
def test_namedtuple():
    class SampleModel(Model):
        field: fields.NamedTuple[str]

    value = namedtuple("SomeNamedTuple", ["x"])("asdf")
    model = SampleModel(field=value)

    assert model.field.as_db_type() == "tuple"
    assert isinstance(model.field.as_db_value(), list)
    assert model.field.data == value
    assert model.field.as_db_value() == list(value)
    assert model.field.as_python_value() == tuple(value)
