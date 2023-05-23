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

from nodeedge.constants import Undefined
from nodeedge.exceptions import InvalidPathError
from nodeedge.query import EnumOperand, EnumLookupExpression
from nodeedge.types import PathDirectionType, UndefinedType
from nodeedge.utils.typing import get_origin, is_subclass, is_class


__all__ = [
    "Cloneable",
    "Valueable",
    "CompositableItem",
    "CompositionListener",
    "Composition",
    "Pathable",
    "Filterable",
]


_BUILD_IN_ATTRS = frozenset(dir(object) + dir(type))

_CloningAttrsType: TypeAlias = Union[FrozenSet[str], Tuple[str, ...]]


class Cloneable(abc.ABC):
    __is_mixin__ = True
    __allow_mixin_operation__ = True
    __cloning_attrs__: _CloningAttrsType = frozenset(["__is_mixin__", "__allow_mixin_operation__"])
    __init_args__: Tuple[str, ...] = ()
    __init_kwargs__: FrozenSet[str] = frozenset()
    __cloning_operator__: Union[Callable[[Self], Self], None] = None

    def __init_subclass__(cls, **kwargs):
        if cls is Cloneable:
            return super().__init_subclass__(**kwargs)

        if getattr(cls, "__allow_mixin_operation__", True):
            _extend_cloning_attrs(cls)
            _extend_cloning_args(cls)

        return super().__init_subclass__(**kwargs)

    __skip_arg_names = frozenset(["__pydantic_self__"])

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
            if name in self.__skip_arg_names:
                continue
            if name in args:
                init_args.append(args[name])
            else:
                init_args.append(getattr(self, name))

        for name in self.__init_kwargs__:
            if name in self.__skip_arg_names:
                continue
            if name in args:
                continue
            if name in kwargs:
                init_kwargs[name] = kwargs[name]
            else:
                init_kwargs[name] = getattr(self, name)

        if callable(self.__cloning_operator__):
            obj = self.__cloning_operator__(self)
        else:
            obj = self.__class__(*init_args, **init_kwargs)  # type: ignore

        for attr in self.__cloning_attrs__:
            if attr in attrs:
                continue
            setattr(obj, attr, getattr(self, attr))

        for attr, value in attrs.items():
            setattr(obj, attr, value)

        return obj

    @staticmethod
    def required_cloneable_inheritance(obj: Any):
        if is_class(obj):
            mro = obj.__mro__
        else:
            mro = obj.__class__.__mro__

        if Cloneable not in mro:
            raise TypeError("required to inherit Cloneable")


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
        if name == "args" and param.kind == param.VAR_POSITIONAL:
            continue
        if name == "kwargs" and param.kind == param.VAR_KEYWORD:
            continue
        if param.kind in [
            param.POSITIONAL_ONLY,
            param.POSITIONAL_OR_KEYWORD,
            param.VAR_POSITIONAL,
        ]:
            init_args.append(name)
        elif param.kind in [param.KEYWORD_ONLY, param.VAR_KEYWORD]:
            init_kwargs.add(name)

    cls.__init_args__ = tuple(init_args)
    cls.__init_kwargs__ = frozenset(init_kwargs)


_Valueable_T = TypeVar("_Valueable_T")


class Valueable(abc.ABC, Generic[_Valueable_T]):
    __is_mixin__ = True
    __allow_mixin_operation__ = True
    __cloning_attrs__: _CloningAttrsType = frozenset(["__value__", "__value_type__"])
    __value__: Union[_Valueable_T, UndefinedType] = Undefined
    __value_type__: Union[FrozenSet[Type], EllipsisType, None] = ...

    @staticmethod
    def required_valueable_inheritance(obj: Any):
        if is_class(obj):
            mro = obj.__mro__
        else:
            mro = obj.__class__.__mro__

        if Valueable not in mro:
            raise TypeError("required to inherit Valueable")

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

    def _clone(self, **kwargs):
        Cloneable.required_cloneable_inheritance(self)
        return super()._clone(**kwargs)  # type: ignore

    @property
    def value(self) -> Union[_Valueable_T, UndefinedType]:
        return self.__value__

    def set_value(
        self, value: _Valueable_T, *, validator: Optional[Callable[[Any], None]] = None
    ) -> Self:
        if callable(validator):
            validator(value)
        else:
            self.check_value(value)

        return self._clone(attrs={"__value__": value})

    def __pos__(self) -> Self:
        if hasattr(self.__value__, "__pos__"):
            return self._clone(attrs={"__value__": +self.__value__})
        raise TypeError(f"bad operand type for unary +: {type(self.__value__).__name__!r}")

    positive = __pos__

    def __neg__(self) -> Self:
        if hasattr(self.__value__, "__neg__"):
            return self._clone(attrs={"__value__": -self.__value__})
        raise TypeError(f"bad operand type for unary -: {type(self.__value__).__name__!r}")

    negative = __neg__


CompositedDirectionType: TypeAlias = Literal["left", "right", ""]

_CompositionItemResult_T = TypeVar("_CompositionItemResult_T")

_CompositableClass_T = TypeVar("_CompositableClass_T", bound="Composition")


class Compositable(abc.ABC, Generic[_CompositionItemResult_T]):
    __is_mixin__ = True
    __allow_mixin_operation__ = True
    __operand__: EnumOperand
    __cloning_attrs__: _CloningAttrsType = frozenset(["__operand__"])

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
    Compositable,
    abc.ABC,
    Generic[_CompositionItemResult_T, _CompositableClass_T],
):
    __operand__: EnumOperand = EnumOperand.AND
    __compositable_class__: Type[_CompositableClass_T]
    __cloning_attrs__: _CloningAttrsType = frozenset(["__operand__", "__compositable_class__"])

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

    def _clone(self, **kwargs):
        Cloneable.required_cloneable_inheritance(self)
        return super()._clone(**kwargs)  # type: ignore

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
    Compositable,
    abc.ABC,
    Generic[_CompositionItemResult_T],
):
    __cloning_attrs__: _CloningAttrsType = frozenset(["__listener__", "__operand__"])

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
        operand = EnumOperand.find_member(operand)
        if not isinstance(operand, EnumOperand):
            raise TypeError("operand must be an instance of EnumOperand")

    def _clone(self, **kwargs):
        Cloneable.required_cloneable_inheritance(self)
        return super()._clone(**kwargs)  # type: ignore

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


class Pathable(abc.ABC):
    __is_mixin__ = True
    __allow_mixin_operation__ = True
    __cloning_attrs__: _CloningAttrsType = frozenset(["__current__", "__backward__", "__forward__"])

    __current__: Union[Pathable, None] = None
    __backward__: Union[Pathable, None] = None
    __forward__: Union[Pathable, None] = None

    def _clone(self, **kwargs):
        Cloneable.required_cloneable_inheritance(self)
        return super()._clone(**kwargs)  # type: ignore

    @classmethod
    def create_path(
        cls,
        current: Pathable,
        *,
        forward: Optional[Pathable] = None,
        backward: Optional[Pathable] = None,
    ) -> Self:
        cls.check_pathable(current, "current")
        if not forward:
            cls.check_pathable(forward, "forward")
        if not backward:
            cls.check_pathable(backward, "backward")

        obj = cls()
        obj.__current__ = current
        obj.__forward__ = forward
        obj.__backward__ = backward
        return obj

    @classmethod
    def check_pathable(cls, other: Any, direction: PathDirectionType) -> Pathable:
        if not isinstance(other, Pathable):
            raise InvalidPathError(f"Cannot compose non-pathable types: {type(other)}({other})")
        return other

    def __rshift__(self, other: Pathable) -> Pathable:
        other = self.check_pathable(other, "forward")
        current: Pathable
        backward: Union[Pathable, None]
        forward: Pathable

        if self.__forward__:
            backward = self
            current = self.__forward__
            forward = other
        else:
            backward = self.__backward__
            current = self
            forward = other

        result = self._clone(
            attrs={"__current__": current, "__backward__": backward, "__forward__": forward}
        )
        return result

    set_forward_path = __rshift__

    def __lshift__(self, other: Pathable) -> Pathable:
        raise NotImplementedError

    set_backward_path = __lshift__

    @property
    def has_path(self) -> bool:
        return bool(self.__forward__ or self.__backward__)

    @property
    def current_path(self) -> Union[Pathable, None]:
        if self.__current__:
            assert isinstance(self.__current__, Pathable)
            return self.__current__

        assert self.__current__ is None
        return self.__current__

    @property
    def backward_path(self) -> Union[Pathable, None]:
        if self.__backward__:
            assert isinstance(self.__backward__, Pathable)
        else:
            assert self.__backward__ is None
        return self.__backward__

    @property
    def forward_path(self) -> Union[Pathable, None]:
        if self.__forward__:
            assert isinstance(self.__forward__, Pathable)
        else:
            assert self.__forward__ is None
        return self.__forward__


_Filterable_T = TypeVar("_Filterable_T")


class Filterable(abc.ABC, Generic[_Filterable_T]):
    __is_mixin__ = True
    __allow_mixin_operation__ = True
    __cloning_attrs__: _CloningAttrsType = frozenset(["__lookup__"])
    __lookup__: EnumLookupExpression = EnumLookupExpression.EQUAL

    def _clone(self, **kwargs):
        Cloneable.required_cloneable_inheritance(self)
        return super()._clone(**kwargs)  # type: ignore

    @property
    def value(self):
        Valueable.required_valueable_inheritance(self)
        return super().value  # type: ignore

    def __invert__(self) -> Self:
        if not self.__lookup__.can_negate_expr():
            raise TypeError(f"Cannot negate {self.__lookup__}")
        lookup = self.__lookup__ | EnumLookupExpression.NOT
        return self._clone(attrs={"__lookup__": lookup})

    def not_(self) -> Self:
        return self.__invert__()

    def exists(self) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.EXISTS})

    def equal(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.EQUAL}).set_value(other)

    def __lt__(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.LT}).set_value(other)

    lt = __lt__

    def __le__(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.LE}).set_value(other)

    le = __le__

    def __gt__(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.GT}).set_value(other)

    gt = __gt__

    def __ge__(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.GE}).set_value(other)

    ge = __ge__

    def like(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.LIKE}).set_value(other)

    def ilike(self, other: _Filterable_T) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.ILIKE}).set_value(other)

    def in_(
        self, other: Union[_Filterable_T | Union[List[_Filterable_T], Tuple[_Filterable_T, ...]]]
    ) -> Self:
        return self._clone(attrs={"__lookup__": EnumLookupExpression.IN}).set_value(
            other, validator=self.__check_value_for_in_expr
        )

    def __check_value_for_in_expr(self, value: Any) -> None:
        Valueable.required_valueable_inheritance(self)
        assert hasattr(self, "check_value")

        if not hasattr(value, "__iter__"):
            value = (value,)

        for each in value:
            self.check_value(each)
