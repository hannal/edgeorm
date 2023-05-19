import datetime
from typing import Type, Any
from decimal import Decimal

import pytest
from pydantic import ValidationError
from pydantic.validators import BOOL_TRUE, BOOL_FALSE

from nodeedge import GlobalConfiguration
from nodeedge.model import fields, Model
from nodeedge.utils.datetime import make_aware

is_backend_edgedb = GlobalConfiguration.is_edgedb_backend()

skip_if_not_edgedb = pytest.mark.skipif(not is_backend_edgedb, reason="not edgedb backend")


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
def test_valid_int(field_type: Type[fields.BaseField], value: int, expected_db_type: str):
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
    field_type: Type[fields.BaseField], value, expected_type, expected_db_type, expected_json_value
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