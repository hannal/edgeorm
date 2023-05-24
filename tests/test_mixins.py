from __future__ import annotations

import dataclasses
from typing import Union, Optional
from unittest.mock import MagicMock

import pytest

from nodeedge.exceptions import InvalidPathError, NotAllowedCompositionError, NotAllowedPathError
from nodeedge.model import Model
from nodeedge.model import fields
from nodeedge.model.fields import Field
from nodeedge.query import EnumOperand, EnumLookupExpression
from nodeedge.mixins import (
    Cloneable,
    Valueable,
    Composition,
    CompositableItem,
    CompositionListener,
    Pathable,
    Filterable,
)


def test_cloneable():
    class Sample(Pathable, Cloneable):
        __cloning_attrs__ = frozenset(["name2"])

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
    assert Sample.__init_args__ == ("value", "value2")
    assert Sample.__init_kwargs__ == frozenset(["value3"])
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
    class Sample(Cloneable, Valueable[int]):
        def __init__(self, value: int) -> None:
            self.check_value(value)
            self.__value__ = value

    with pytest.raises(TypeError):
        Sample("hello")

    origin = Sample(10)
    assert origin.value == 10

    obj = origin.set_value(20)
    assert origin is not obj
    assert origin.value != obj.value
    assert obj.value == 20

    obj2 = -obj
    assert obj is not obj2
    assert obj.value == 20
    assert obj2.value == -20

    obj3 = -obj2
    assert obj2 is not obj3
    assert obj3.value == 20
    assert obj2.value == -20


def test_composite():
    class CompositedItem(Composition):
        pass

    @dataclasses.dataclass(frozen=True)
    class Item(CompositableItem[dict, CompositedItem]):
        name: str

    item1 = Item("hello")
    item2 = Item("world")
    composited = item1 & item2
    assert isinstance(composited, CompositedItem)


@pytest.fixture
def composition_listener():
    mock = MagicMock()
    queries = []

    def on_composite(item, operand, direction, depth):
        mock.on_composite()
        if item and operand:
            queries.append(item)
        elif item and not operand:
            queries.append(item)
        elif not item and operand:
            queries.append(operand)
        return None

    def on_begin_wrap(depth, item):
        mock.on_begin_wrap()
        queries.append("(")
        return None

    def on_finish_wrap(depth, item):
        mock.on_finish_wrap()
        queries.append(")")
        return

    listener = CompositionListener(
        on_composite=on_composite,
        on_begin_wrap=on_begin_wrap,
        on_finish_wrap=on_finish_wrap,
    )
    return listener, mock, queries


def test_simple_composition_map(composition_listener):
    listener, mock, queries = composition_listener

    class CompositedItem(Composition):
        __listener__ = listener

        def on_composite(self, depth=0, direction=""):
            return f"composited<{depth}, {direction}>"

    @dataclasses.dataclass(frozen=True)
    class Item(CompositableItem[str, CompositedItem]):
        name: str

        def on_composite(self, depth=0, direction=""):
            return f"item<{self.name}, {depth}, {direction}>"

    item1 = Item("hello")
    item2 = Item("world")
    composited = item1 & item2
    composited.map_composition()

    # fmt: off
    expected = [
        "(",
            item1,
            EnumOperand.AND,
            item2,
        ")",
    ]
    # fmt: on

    mock.on_composite.assert_called()
    mock.on_begin_wrap.assert_called()
    mock.on_finish_wrap.assert_called()

    assert queries == expected


def test_complex_composition_map(composition_listener):
    listener, mock, queries = composition_listener

    class CompositedItem(Composition):
        __listener__ = listener

    @dataclasses.dataclass(frozen=True)
    class Item(CompositableItem[str, CompositedItem]):
        name: str

    item1 = Item("hello")
    item2 = Item("world")
    item3 = Item("lorem")
    item4 = Item("ipsum")
    composited = item1 | item2 & (item3 | item4)
    assert composited.left == item1
    assert isinstance(composited.right, CompositedItem)
    assert composited.right.left == item2
    assert isinstance(composited.right.right, CompositedItem)
    assert composited.right.right.left == item3
    assert composited.right.right.right == item4

    # fmt: off
    expected = [
        "(",
            item1,
            EnumOperand.OR,
            "(",
                item2,
                EnumOperand.AND,
                "(",
                    item3,
                    EnumOperand.OR,
                    item4,
                ")",
            ")",
        ")",
    ]
    # fmt: on

    composited.map_composition()

    mock.on_composite.assert_called()
    mock.on_begin_wrap.assert_called()
    mock.on_finish_wrap.assert_called()

    assert queries == expected


def test_pathable():
    class Sample1(Cloneable, Pathable):
        name = 1

    class Sample2(Cloneable, Pathable):
        name = 2

    obj1 = Sample1()
    obj2 = Sample2()

    path = obj1 >> obj2
    assert path.has_path
    assert not obj1.has_path
    assert not obj2.has_path
    assert path.__current__ == obj1
    assert path.__forward__ == obj2
    assert path.__backward__ is None


def test_make_path_for_model_field():
    class SampleModel1(Model):
        name: fields.Str

    class SampleModel2(Model):
        name: fields.Str
        link_to: fields.Link[SampleModel1, None]

    SampleModel2.update_forward_refs(SampleModel1=SampleModel1)

    obj1 = SampleModel1(name="hello")
    obj2 = SampleModel2(name="world", link_to=obj1)

    with pytest.raises(TypeError) as exc:
        obj1 >> obj2

    assert "right operand of '>>'" in str(exc.value)

    with pytest.raises(InvalidPathError):
        SampleModel2.link_to >> obj1

    with pytest.raises(NotAllowedPathError):
        SampleModel2.link_to >> obj1.name

    path = SampleModel2.link_to >> SampleModel1.name
    assert path.has_path
    assert not obj1.has_path
    assert not obj2.has_path
    assert path.current_path == SampleModel2.link_to
    assert path.forward_path == SampleModel1.name
    assert path.backward_path is None

    class SampleModel3(Model):
        name: fields.Str
        path_to: fields.Link[SampleModel2, None]

    SampleModel3.update_forward_refs(SampleModel2=SampleModel2)

    path = SampleModel3.path_to >> SampleModel2.link_to >> SampleModel2.name
    assert path.has_path
    assert path.backward_path == SampleModel3.path_to
    assert path.current_path == SampleModel2.link_to
    assert path.forward_path == SampleModel2.name


def test_filterable(composition_listener):
    listener, *_ = composition_listener

    class SampleModel(Model):
        name: fields.Str

    class CompositedItem(Composition):
        __listener__ = listener

    class Filter(Filterable[Field], Valueable, Cloneable, CompositableItem[Field, CompositedItem]):
        def __init___(self, value, lookup: Optional = None):
            self.check_value(value)
            self.__value__ = value

    field1 = SampleModel.name.set_value("hello")
    field2 = SampleModel.name.set_value("world")
    filter1 = Filter.create_filter(field1)
    filter2 = Filter.create_filter(field2)
    assert filter1.value == field1
    assert filter2.value == field2
    assert filter1.filter_lookup == filter2.filter_lookup == EnumLookupExpression.EQUAL

    composited = filter1 & filter2
    assert composited.left == filter1
    assert composited.right == filter2
    assert composited.operand == EnumOperand.AND

    with pytest.raises(NotAllowedCompositionError):
        filter1 & field2
