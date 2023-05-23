from nodeedge.types import enum
from nodeedge.utils.typing import is_subclass


def test_extended_enum():
    @enum.create(enum_class=enum.Flag)
    class Sample:
        A: enum.Auto
        B: enum.Auto
        C: enum.Auto

    assert is_subclass(Sample, enum.Flag)

    composited = Sample.A | Sample.B
    assert composited & Sample.A == Sample.A

    assert hasattr(Sample.A, "as_jsonable_value")
    assert Sample.A.as_jsonable_value() == Sample.A.name

    for v in [Sample.A, Sample.A.name, Sample.A.value]:
        assert Sample.find_member(v) == Sample.A
        assert Sample.A.find_member(v) == Sample.A
