from __future__ import annotations

import abc
import dataclasses
import inspect
from types import EllipsisType
from typing import (
    FrozenSet,
    Tuple,
    Optional,
    Dict,
    Union,
    List,
    Set,
    TypeVar,
    Generic,
    Any,
    Type,
    Literal,
    Callable,
    cast,
)

from typing_extensions import Self, TypeAlias

from nodeedge.constants import EnumOperand
from nodeedge.utils.typing import get_origin, is_subclass


__all__ = [
    "Cloneable",
    "Valueable",
    "CompositableItem",
    "Composition",
    "CompositionListener",
]


class Cloneable(abc.ABC):
    __cloning_attrs: Union[FrozenSet[str], Tuple[str, ...]] = frozenset()
    __init_args: Tuple[str, ...] = ()
    __init_kwargs: FrozenSet[str] = frozenset()

    def __new__(cls, *args, **kwargs):
        if not isinstance(
            cls.__cloning_attrs,
            (frozenset, tuple),
        ):
            raise TypeError(f"{cls.__name__}._cloning_attrs must be a frozenset or tuple")

        sig = inspect.signature(cls.__init__)
        init_args: List[str] = []
        init_kwargs: Set[str] = set()
        for name, param in sig.parameters.items():
            if name == "self":
                continue
            if param.kind in [
                param.POSITIONAL_ONLY,
                param.VAR_POSITIONAL,
                param.POSITIONAL_OR_KEYWORD,
            ]:
                init_args.append(name)
            elif param.kind in [param.VAR_KEYWORD, param.KEYWORD_ONLY]:
                init_kwargs.add(name)

        cls.__init_args = tuple(init_args)
        cls.__init_kwargs = frozenset(init_kwargs)

        return super().__new__(cls)

    def _clone(
        self,
        *,
        args: Optional[Dict] = None,
        kwargs: Optional[Dict] = None,
        attrs: Optional[Dict] = None,
    ) -> Self:
        init_args = []
        init_kwargs = {}

        args = args or {}
        kwargs = kwargs or {}
        attrs = attrs or {}

        for name in self.__init_args:
            if name in args:
                init_args.append(args[name])
            else:
                init_args.append(getattr(self, name))

        for name in self.__init_kwargs:
            if name in args:
                continue
            if name in kwargs:
                init_kwargs[name] = kwargs[name]
            else:
                init_kwargs[name] = getattr(self, name)

        obj = self.__class__(*init_args, **init_kwargs)

        for attr in self.__cloning_attrs:
            if attr in attrs:
                continue
            setattr(obj, attr, getattr(self, attr))

        for attr, value in attrs.items():
            setattr(obj, attr, value)

        return obj


_Valueable_T = TypeVar("_Valueable_T")


class Valueable(Cloneable, abc.ABC, Generic[_Valueable_T]):
    __slots__ = ("__value",)

    __value: _Valueable_T
    __value_type: Union[FrozenSet[Type], EllipsisType, None] = ...

    def __init__(self, value: _Valueable_T) -> None:
        self._set_value_type()
        self._check_value_type(value)
        self.__value = value

    def _set_value_type(self):
        if self.__value_type is not ...:
            return None
        for _base in getattr(self, "__orig_bases__", ()):
            if get_origin(_base) is Valueable:
                self.__value_type = frozenset(_base.__args__)
                return None

        self.__value_type = None
        return None

    def _check_value_type(self, value: Any):
        if self.__value_type is ...:
            self._set_value_type()
        if not self.__value_type:
            return None
        if type(value) not in cast(frozenset, self.__value_type):
            raise TypeError(f"bad operand type for bind: {type(value).__name__!r}")

    @property
    def value(self) -> _Valueable_T:
        return self.__value

    def set_value(self, value: _Valueable_T) -> Self:
        self._check_value_type(value)
        return self._clone(args={"value": value})

    def __pos__(self) -> Self:
        if hasattr(self.__value, "__pos__"):
            return self._clone(args={"value": +self.__value})
        raise TypeError(f"bad operand type for unary +: {type(self.__value).__name__!r}")

    positive = __pos__

    def __neg__(self) -> Self:
        if hasattr(self.__value, "__neg__"):
            return self._clone(args={"value": -self.__value})
        raise TypeError(f"bad operand type for unary -: {type(self.__value).__name__!r}")

    negative = __neg__


CompositedDirectionType: TypeAlias = Literal["left", "right", ""]

_CompositionItemResult_T = TypeVar("_CompositionItemResult_T")

_CompositableClass_T = TypeVar("_CompositableClass_T", bound="Composition")


class Compositable(abc.ABC, Generic[_CompositionItemResult_T]):
    _operand: EnumOperand

    @property
    def operand(self) -> EnumOperand:
        return self._operand

    @operand.setter
    def operand(self, value: EnumOperand):
        if not isinstance(value, EnumOperand):
            raise TypeError("operand must be an instance of EnumOperand")
        self._operand = value

    @staticmethod
    def _check_compositable(other: Compositable):
        if not isinstance(other, Compositable):
            raise TypeError("other must be an instance of Compositable")

    @abc.abstractmethod
    def __and__(self, other: Compositable):
        raise NotImplementedError

    def and_(self, other: Compositable):
        return self.__and__(other)

    def __rand__(self, other: Compositable):
        return self.__and__(other)

    @abc.abstractmethod
    def __or__(self, other: Compositable):
        raise NotImplementedError

    def or_(self, other: Compositable):
        return self.__or__(other)

    def __ror__(self, other: Compositable):
        return self.__or__(other)


class CompositableItem(
    Cloneable,
    Compositable,
    abc.ABC,
    Generic[_CompositionItemResult_T, _CompositableClass_T],
):
    __slots__ = ()

    _operand: EnumOperand = EnumOperand.AND
    __compositable_class: Type[_CompositableClass_T]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for _base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(_base)
            if origin is not CompositableItem:
                continue

            for _t in _base.__args__:
                if is_subclass(_t, Composition):
                    compositable_class = _t
                    cls.__compositable_class = compositable_class
                    return None

        raise TypeError("CompositableItem subclass must be a subclass of Composition")

    def __hash__(self):
        return hash((self.__class__, id(self), self.operand))

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.__hash__()}>"

    __str__ = __repr__

    def __and__(self, other: Compositable) -> _CompositableClass_T:
        self._check_compositable(other)
        return self.__compositable_class(self, EnumOperand.AND, other)

    def __or__(self, other: Compositable) -> _CompositableClass_T:
        self._check_compositable(other)
        return self.__compositable_class(self, EnumOperand.OR, other)


OnCompositionType: TypeAlias = Callable[
    [Compositable, Optional[EnumOperand], Optional[CompositedDirectionType], Optional[int]],
    _CompositionItemResult_T,
]


@dataclasses.dataclass(frozen=True, kw_only=True)
class CompositionListener:
    on_composite: Callable[
        [
            Union[Compositable, None],
            Optional[EnumOperand],
            Optional[CompositedDirectionType],
            Optional[int],
        ],
        _CompositionItemResult_T,
    ]
    on_begin_wrap: Callable[
        [int, Optional[Compositable]],
        None,
    ]
    on_finish_wrap: Callable[
        [int, Optional[Compositable]],
        None,
    ]


_default_composition_listener = CompositionListener(
    on_composite=lambda item, operand=None, direction=None, depth=None: None,  # type: ignore
    on_begin_wrap=lambda depth, item=None: None,  # type: ignore
    on_finish_wrap=lambda depth, item=None: None,  # type: ignore
)


class Composition(
    Cloneable,
    Compositable,
    abc.ABC,
    Generic[_CompositionItemResult_T],
):
    __slots__ = ("__attr_prefix", "__left_attr_name", "__right_attr_name")

    __left: Compositable
    __right: Compositable
    _listener: CompositionListener = _default_composition_listener
    _operand: EnumOperand = EnumOperand.AND

    def __init__(self, left: Compositable, operand: EnumOperand, right: Compositable) -> None:
        if not isinstance(left, Compositable) or not isinstance(right, Compositable):
            raise TypeError("Cannot compose non-compositable types")

        self.__left = left
        self.__right = right
        self._operand = operand

        for _t in self.__class__.__mro__[2:]:
            if _t.__module__ == self.__module__:
                base = _t
                break
        else:
            base = self.__class__.__base__

        self.__attr_prefix = f"_{base.__name__}__"
        self.__left_attr_name = f"{self.__attr_prefix}left"
        self.__right_attr_name = f"{self.__attr_prefix}right"

        self.__cloning_attrs = frozenset(
            f"{self.__attr_prefix}{_n}"
            for _n in ["__listener", "__attr_prefix", "__left_attr_name", "__right_attr_name"]
        )

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__left}, {self.operand}, {self.__right})"

    def __and__(self, other: Compositable) -> Self:
        self._check_compositable(other)
        return self._clone(args={"left": self, "operand": EnumOperand.AND, "right": other})

    def __or__(self, other: Compositable) -> Self:
        self._check_compositable(other)
        return self._clone(args={"left": self, "operand": EnumOperand.OR, "right": other})

    def map(self, listener: Optional[CompositionListener] = None) -> None:
        """
        depth: composition depth
        """
        depth = 0

        _listener = listener or self._listener or _default_composition_listener

        def _traverse(
            item: Union[Compositable, None],
            direction: CompositedDirectionType = "",
            operand: Optional[EnumOperand] = None,
            each_depth: int = 0,
        ):
            nonlocal depth

            if not item:
                return

            each_depth = abs(each_depth)
            left = getattr(item, self.__left_attr_name, None)
            right = getattr(item, self.__right_attr_name, None)
            if not isinstance(item, Composition) and isinstance(item, Compositable):
                if operand and direction == "right":
                    _listener.on_composite(None, operand, direction, each_depth)

                _listener.on_composite(item, None, direction, each_depth)
                return None

            if direction == "right":
                _listener.on_composite(None, operand, direction, each_depth)

            left_depth = depth - int(isinstance(left, Composition))
            right_depth = depth - int(isinstance(right, Composition))
            depth -= 1

            _listener.on_begin_wrap(each_depth, item)
            _traverse(left, "left", item.operand, left_depth)
            _traverse(right, "right", item.operand, right_depth)
            _listener.on_finish_wrap(each_depth, item)

        _traverse(self)

    @property
    def left(self):
        return self.__left

    @property
    def right(self):
        return self.__right
