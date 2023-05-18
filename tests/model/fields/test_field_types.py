import pytest

from nodeedge.model import fields


def test_str():
    field = fields.Str("hello world")
    assert field.as_db_type() == "str"
    assert field.as_db_value() == "hello world"
    assert field.as_python_value() == "hello world"
    assert field.as_jsonable_value() == '"hello world"'
