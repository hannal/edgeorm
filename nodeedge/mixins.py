import abc
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
    cast,
)

from typing_extensions import Self

from nodeedge.utils.typing import get_origin


__all__ = [
    "Cloneable",
    "Valueable",
]


class Cloneable(abc.ABC):
    _cloning_attrs: Union[FrozenSet[str], Tuple[str, ...]] = frozenset()
    _init_args: Tuple[str, ...] = ()
    _init_kwargs: FrozenSet[str] = frozenset()

    def __new__(cls, *args, **kwargs):
        if not isinstance(
            cls._cloning_attrs,
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

        cls._init_args = tuple(init_args)
        cls._init_kwargs = frozenset(init_kwargs)

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

        for name in self._init_args:
            if name in args:
                init_args.append(args[name])
            else:
                init_args.append(getattr(self, name))

        for name in self._init_kwargs:
            if name in args:
                continue
            if name in kwargs:
                init_kwargs[name] = kwargs[name]
            else:
                init_kwargs[name] = getattr(self, name)

        obj = self.__class__(*init_args, **init_kwargs)

        for attr in self._cloning_attrs:
            if attr in attrs:
                continue
            setattr(obj, attr, getattr(self, attr))

        for attr, value in attrs.items():
            setattr(obj, attr, value)

        return obj


_Valueable_T = TypeVar("_Valueable_T")


class Valueable(Cloneable, abc.ABC, Generic[_Valueable_T]):
    __slots__ = ("_mixin_value",)

    _mixin_value: _Valueable_T
    _mixin_value_type: Union[FrozenSet[Type], EllipsisType, None] = ...

    def __init__(self, value: _Valueable_T) -> None:
        self._set_value_type()
        self._check_value_type(value)
        self._mixin_value = value

    def _set_value_type(self):
        if self._mixin_value_type is not ...:
            return None
        for _base in getattr(self, "__orig_bases__", ()):
            if get_origin(_base) is Valueable:
                self._mixin_value_type = frozenset(_base.__args__)
                return None

        self._mixin_value_type = None
        return None

    def _check_value_type(self, value: Any):
        if self._mixin_value_type is ...:
            self._set_value_type()
        if not self._mixin_value_type:
            return None
        if type(value) not in cast(frozenset, self._mixin_value_type):
            raise TypeError(f"bad operand type for bind: {type(value).__name__!r}")

    @property
    def value(self) -> _Valueable_T:
        return self._mixin_value

    @value.setter
    def value(self, value: Any) -> Self:
        return self.bind(value)

    def bind(self, value: _Valueable_T) -> Self:
        self._check_value_type(value)
        return self._clone(args={"value": value})

    set = bind

    def __pos__(self) -> Self:
        if hasattr(self._mixin_value, "__pos__"):
            return self._clone(args={"value": +self._mixin_value})
        raise TypeError(f"bad operand type for unary +: {type(self._mixin_value).__name__!r}")

    positive = __pos__

    def __neg__(self) -> Self:
        if hasattr(self._mixin_value, "__neg__"):
            return self._clone(args={"value": -self._mixin_value})
        raise TypeError(f"bad operand type for unary -: {type(self._mixin_value).__name__!r}")

    negative = __neg__
