from typing import Union

import pytest

from nodeedge.mixins import Cloneable, Valueable


def test_cloneable():
    class Sample(Cloneable):
        _cloning_attrs = frozenset(["name2"])

        value: int
        value2: int
        value3: int
        name: Union[str, None] = None
        name2: str = "hello"

        def __init__(self, value: int, /, value2: int, *, value3: int = 0) -> None:
            self.value = value
            self.value2 = value2
            self.value3 = value3

        def set_name(self, value: Union[str, None]):
            return self._clone(attrs={"name": value})

    origin = Sample(10, 20)
    assert origin._init_args == ("value", "value2")
    assert origin._init_kwargs == frozenset(["value3"])
    assert origin.value == 10
    assert origin.value2 == 20
    assert origin.value3 == 0
    assert origin.name is None
    assert origin.name2 == Sample.name2

    obj = origin.set_name("test")
    assert origin is not obj
    assert origin.value == obj.value
    assert origin.value2 == obj.value2
    assert origin.name != obj.name
    assert origin.name2 == obj.name2


def test_valueable():
    class Sample(Valueable[str]):
        pass

    with pytest.raises(TypeError):
        Sample(10)

    origin = Sample("hello")
    assert origin.value == "hello"

    obj = origin.bind("world")
    assert origin is not obj
    assert origin.value != obj.value
    assert obj.value == "world"
