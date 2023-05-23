import inspect
import itertools
from inspect import isclass, Parameter
from functools import partial, update_wrapper
from typing import Any, Type, Union, Tuple, Dict, Iterable

from pydantic import typing as pydantic_typing


get_args = pydantic_typing.get_args

get_class = pydantic_typing.get_class

get_origin = pydantic_typing.get_origin

is_union = pydantic_typing.is_union

get_all_type_hints = pydantic_typing.get_all_type_hints

__all__ = [
    "is_class",
    "is_union",
    "get_args",
    "get_class",
    "get_origin",
    "get_all_type_hints",
    "annotate_from",
    "is_subclass",
    "sort_function_parameters",
]


def is_class(obj: Any):
    if isclass(obj):
        assert isinstance(type(obj), type)
        return obj
    return False


def is_subclass(obj: Any, target: Union[Type, Tuple[Type, ...]]):
    if not is_class(obj):
        raise TypeError("is_subclass() arg 1 must be a class")
    if not is_class(target) and not isinstance(target, tuple) and not get_args(target):
        raise TypeError("is_subclass() arg 2 must be a class, a tuple of classes, or a union")

    assert isinstance(type(obj), type)

    try:
        assert issubclass(obj, target)
        return True
    except AssertionError:
        return False


def annotate_from(fn):
    """supertype의 annotation을 가져와서 subtype에 적용합니다.
    class Parent:
        def age(self) -> int:
            ...


    class Child(Parent):
        @annotate_from(Parent.age)
        def age(self):
            ...
    """
    return partial(update_wrapper, wrapped=fn, assigned=("__annotations__",), updated=())


def sort_function_parameters(params: Dict[inspect._ParameterKind, Iterable[Parameter]]):
    param_kind_seq = (
        Parameter.POSITIONAL_ONLY,
        Parameter.POSITIONAL_OR_KEYWORD,
        Parameter.VAR_POSITIONAL,
        Parameter.KEYWORD_ONLY,
        Parameter.VAR_KEYWORD,
    )
    return itertools.chain.from_iterable([params[kind] for kind in param_kind_seq])
