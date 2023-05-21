from __future__ import annotations

import abc
import dataclasses
import inspect
from functools import cached_property
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
    "CompositionListener",
    "Composition",
    "Pathable",
]


class Cloneable(abc.ABC):
    __cloning_attrs__: Union[FrozenSet[str], Tuple[str, ...]] = frozenset()
    __init_args__: Tuple[str, ...] = ()
    __init_kwargs__: FrozenSet[str] = frozenset()

    def __init_subclass__(cls, **kwargs):
        if cls is Cloneable:
            return super().__init_subclass__(**kwargs)

        _extend_cloning_attrs(cls)
        _extend_cloning_args(cls)

        return super().__init_subclass__(**kwargs)

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

        for name in self.__init_args__:
            if name in args:
                init_args.append(args[name])
            else:
                init_args.append(getattr(self, name))

        for name in self.__init_kwargs__:
            if name in args:
                continue
            if name in kwargs:
                init_kwargs[name] = kwargs[name]
            else:
                init_kwargs[name] = getattr(self, name)

        obj = self.__class__(*init_args, **init_kwargs)  # type: ignore

        for attr in self.__cloning_attrs__:
            if attr in attrs:
                continue
            setattr(obj, attr, getattr(self, attr))

        for attr, value in attrs.items():
            setattr(obj, attr, value)

        return obj


def _extend_cloning_attrs(cls):
    attr_name = "__cloning_attrs__"
    cloning_attrs = frozenset(getattr(cls, attr_name, []))
    for _t in cls.__bases__:
        if _t in [Cloneable, abc.ABC, abc.ABCMeta]:
            continue

        attr = getattr(_t, attr_name, None)
        if isinstance(attr, (tuple, set)):
            cloning_attrs = cloning_attrs.union(frozenset(attr))
        elif isinstance(attr, frozenset):
            cloning_attrs = cloning_attrs.union(attr)

    setattr(cls, attr_name, cloning_attrs)


def _extend_cloning_args(cls):
    if not isinstance(getattr(cls, "__cloning_attrs__", None), (frozenset, tuple)):
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

    cls.__init_args__ = tuple(init_args)
    cls.__init_kwargs__ = frozenset(init_kwargs)


_Valueable_T = TypeVar("_Valueable_T")


class Valueable(Cloneable, abc.ABC, Generic[_Valueable_T]):
    __slots__ = ("__value__",)

    __value__: _Valueable_T
    __value_type__: Union[FrozenSet[Type], EllipsisType, None] = ...

    def __set_value_type(self):
        if self.__value_type__ is not ...:
            return None
        for _base in getattr(self, "__orig_bases__", ()):
            if get_origin(_base) is Valueable:
                self.__value_type__ = frozenset(_base.__args__)
                return None

        self.__value_type__ = None
        return None

    def check_value(self, value: Any):
        self.__set_value_type()
        if self.__value_type__ is ...:
            self.__set_value_type()
        if not self.__value_type__:
            return None
        if type(value) not in cast(frozenset, self.__value_type__):
            raise TypeError(f"bad operand type for bind: {type(value).__name__!r}")

    @property
    def value(self) -> _Valueable_T:
        return self.__value__

    def set_value(self, value: _Valueable_T) -> Self:
        self.check_value(value)
        return self._clone(args={"value": value})

    def __pos__(self) -> Self:
        if hasattr(self.__value__, "__pos__"):
            return self._clone(args={"value": +self.__value__})
        raise TypeError(f"bad operand type for unary +: {type(self.__value__).__name__!r}")

    positive = __pos__

    def __neg__(self) -> Self:
        if hasattr(self.__value__, "__neg__"):
            return self._clone(args={"value": -self.__value__})
        raise TypeError(f"bad operand type for unary -: {type(self.__value__).__name__!r}")

    negative = __neg__


CompositedDirectionType: TypeAlias = Literal["left", "right", ""]

_CompositionItemResult_T = TypeVar("_CompositionItemResult_T")

_CompositableClass_T = TypeVar("_CompositableClass_T", bound="Composition")


class Compositable(abc.ABC, Generic[_CompositionItemResult_T]):
    __operand__: EnumOperand

    @property
    def operand(self) -> EnumOperand:
        return self.__operand__

    @operand.setter
    def operand(self, value: EnumOperand):
        if not isinstance(value, EnumOperand):
            raise TypeError("operand must be an instance of EnumOperand")
        self.__operand__ = value

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

    __operand__: EnumOperand = EnumOperand.AND
    __compositable_class__: Type[_CompositableClass_T]

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        for _base in getattr(cls, "__orig_bases__", ()):
            origin = get_origin(_base)
            if origin is not CompositableItem:
                continue

            for _t in _base.__args__:
                if is_subclass(_t, Composition):
                    compositable_class = _t
                    cls.__compositable_class__ = compositable_class
                    return None

        raise TypeError("CompositableItem subclass must be a subclass of Composition")

    def __hash__(self):
        return hash((self.__class__, id(self), self.operand))

    def __repr__(self):
        return f"{self.__class__.__name__}<{self.__hash__()}>"

    __str__ = __repr__

    def __and__(self, other: Compositable) -> _CompositableClass_T:
        self._check_compositable(other)
        return self.__compositable_class__.create_composition(self, EnumOperand.AND, other)

    def __or__(self, other: Compositable) -> _CompositableClass_T:
        self._check_compositable(other)
        return self.__compositable_class__.create_composition(self, EnumOperand.OR, other)


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
    __slots__ = ()
    __cloning_attrs__ = frozenset(["__listener__", "__operand__"])

    __left__: Compositable
    __right__: Compositable
    __listener__: CompositionListener = _default_composition_listener
    __operand__: EnumOperand = EnumOperand.AND

    @classmethod
    def create_composition(
        cls, left: Compositable, operand: EnumOperand, right: Compositable
    ) -> Self:
        cls.check_composition_args(left, operand, right)
        obj = cls()
        obj.__left__ = left
        obj.__right__ = right
        obj.__operand__ = operand
        return obj

    @classmethod
    def check_composition_args(cls, left: Compositable, operand: EnumOperand, right: Compositable):
        if not isinstance(left, Compositable) or not isinstance(right, Compositable):
            raise TypeError("Cannot compose non-compositable types")
        if not isinstance(operand, EnumOperand):
            raise TypeError("operand must be an instance of EnumOperand")

    def __repr__(self):
        return f"{self.__class__.__name__}({self.__left__}, {self.operand}, {self.__right__})"

    def __and__(self, other: Compositable) -> Self:
        self._check_compositable(other)
        return self._clone(args={"left": self, "operand": EnumOperand.AND, "right": other})

    def __or__(self, other: Compositable) -> Self:
        self._check_compositable(other)
        return self._clone(args={"left": self, "operand": EnumOperand.OR, "right": other})

    def map_composition(self, listener: Optional[CompositionListener] = None) -> None:
        """
        depth: composition depth
        """
        depth = 0

        _listener = listener or self.__listener__ or _default_composition_listener

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
            left = getattr(item, "__left__", None)
            right = getattr(item, "__right__", None)
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
        return self.__left__

    @property
    def right(self):
        return self.__right__


class Pathable(Cloneable, abc.ABC):
    __cloning_attrs__ = frozenset(["__current__", "__backward__", "__forward__"])

    __current__: Union[Pathable, None] = None
    __backward__: Union[Pathable, None] = None
    __forward__: Union[Pathable, None] = None

    @classmethod
    def create_path(
        cls,
        current: Pathable,
        *,
        forward: Optional[Pathable] = None,
        backward: Optional[Pathable] = None,
    ) -> Self:
        cls.check_pathable(current)
        if not forward:
            cls.check_pathable(forward)
        if not backward:
            cls.check_pathable(backward)

        obj = cls()
        obj.__current__ = current
        obj.__forward__ = forward
        obj.__backward__ = backward
        return obj

    @staticmethod
    def check_pathable(other: Any):
        if not isinstance(other, Pathable):
            raise TypeError("Cannot compose non-pathable types")

    def __rshift__(self, other: Pathable) -> Pathable:
        self.check_pathable(other)
        return self._clone(args={"current": self, "forward": other})

    forward_path = __rshift__

    def __lshift__(self, other: Pathable) -> Pathable:
        self.check_pathable(other)
        return self._clone(args={"current": self, "backward": other})

    backward_path = __lshift__

    @cached_property
    def has_path(self) -> bool:
        return bool(self.__forward__ or self.__backward__)
