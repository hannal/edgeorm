from inspect import isclass
from functools import partial, update_wrapper

from pydantic import typing as pydantic_typing

is_class = isclass

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
]


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
