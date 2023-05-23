from __future__ import annotations

import abc
import dataclasses
import enum as py_enum
from collections import OrderedDict
from types import new_class
from typing import (
    Mapping,
    Type,
    Dict,
    Any,
    Optional,
    Iterable,
    TypeVar,
    Iterator,
    Union,
    Hashable,
    cast,
)

from pydantic.fields import FieldInfo as _PydanticFieldInfo
from pydantic.fields import UndefinedType
from typing_extensions import TYPE_CHECKING

from ._enum import JsonableEnum, FindableEnum
from ..constants import Undefined

if TYPE_CHECKING:
    from ..model.fields import NodeEdgeFieldInfo


__all__ = [
    "BaseFilterable",
    "ImmutableDict",
    "ValueClass",
    "UndefinedType",
    "FieldInfo",
    "Query",
    "Jsonable",
    "enum",
]


class BaseFilterable:
    pass


_KT = TypeVar("_KT", bound=Hashable)
_KV = TypeVar("_KV")


class ImmutableDict(Mapping[_KT, _KV]):
    _dict_cls: Type[Dict[_KT, _KV]]

    def __init__(self, *args: Any, dict_cls=OrderedDict, **kwargs: Any) -> None:
        self._dict_cls = dict_cls
        self._dict = self._dict_cls(*args, **kwargs)
        self._hash: Optional[int] = None

    @classmethod
    def fromkeys(cls, seq: Iterable[_KT], value: Optional[_KV] = None) -> ImmutableDict[_KT, _KV]:
        return cls(dict.fromkeys(seq, value))

    def __getitem__(self, key: _KT) -> _KV:
        return self._dict[key]

    def __contains__(self, key: object) -> bool:
        return key in self._dict

    def copy(self, **kwargs) -> ImmutableDict[_KT, _KV]:
        return self.__class__(self, **kwargs)

    def __iter__(self) -> Iterator[_KT]:
        return iter(self._dict)

    def __len__(self) -> int:
        return len(self._dict)

    def __repr__(self) -> str:
        return "{name}({repr})".format(name=self.__class__.__name__, repr=self._dict)

    def __hash__(self) -> int:
        if self._hash is not None:
            return self._hash

        value = 0
        for _key, _value in self.items():
            value ^= hash((_key, _value))
        self._hash = value

        return self._hash

    def __or__(self, other: Any) -> ImmutableDict[_KT, _KV]:
        if not isinstance(other, (dict, self.__class__)):
            return NotImplemented
        new = dict(self)
        new.update(other)
        return self.__class__(new)

    def __ror__(self, other: Any) -> Dict[Any, Any]:
        if not isinstance(other, (dict, self.__class__)):
            return NotImplemented
        new = dict(other)
        new.update(self)
        return new

    def __ior__(self, other: Any) -> ImmutableDict[_KT, _KV]:
        raise TypeError(f"'{self.__class__.__name__}' object is not mutable")


class ValueClass(type):
    def __call__(cls, *args, **kwargs):
        raise TypeError(f"{cls.__name__} cannot be instantiated")


class FieldInfo(_PydanticFieldInfo):
    def __init__(
        self,
        default: Any = Undefined,
        *,
        nodeedge: Optional[NodeEdgeFieldInfo] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(default=default, nodeedge=nodeedge, **kwargs)

    @property
    def nodeedge(self) -> Union[NodeEdgeFieldInfo, None]:
        return self.extra.get("nodeedge")


@dataclasses.dataclass
class Query:
    pass


class Jsonable:
    @abc.abstractmethod
    def as_jsonable_value(self) -> Any:
        raise NotImplementedError


T_EnumClass = TypeVar("T_EnumClass", bound=Type[py_enum.Enum])
T_TargetEnum = TypeVar("T_TargetEnum", bound=Type)


class _BaseEnum(FindableEnum, JsonableEnum):
    pass


class enum:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("enum() is not intended to be instantiated directly.")

    class Flag(_BaseEnum, py_enum.Flag):
        def __and__(self, other: Any) -> Any:
            return super().__and__(other)

        __rand__ = __and__

        def __or__(self, other: Any) -> Any:
            return super().__or__(other)

        __ror__ = __or__

    class IntFlag(_BaseEnum, py_enum.IntFlag):  # type: ignore
        def __and__(self, other: Any) -> Any:
            return super().__and__(other)

        __rand__ = __and__

        def __or__(self, other: Any) -> Any:
            return super().__or__(other)

        __ror__ = __or__

    class Enum(_BaseEnum, py_enum.Enum):
        pass

    class IntEnum(_BaseEnum, py_enum.IntEnum):
        pass

    class StrEnum(_BaseEnum, py_enum.StrEnum):
        pass

    class BaseEnum(_BaseEnum):
        pass

    class Auto(py_enum.auto, _BaseEnum):  # type: ignore
        def as_jsonable_value(self) -> Any:
            return self.name

        def __and__(self, other: Any) -> Any:
            return super().__and__(other)

    @classmethod
    def auto(cls, *args, **kwargs):
        return cls.Auto(*args, **kwargs)

    @classmethod
    def create(
        cls,
        target_class: Optional[T_TargetEnum] = None,
        *,
        enum_class: T_EnumClass,
    ):
        def wrap(_target_cls: T_TargetEnum) -> T_TargetEnum:
            members = []
            for k, v in _target_cls.__annotations__.items():
                if v is cls.Auto:
                    members.append((k, py_enum.auto()))
                elif isinstance(v, cls.Auto):
                    members.append((k, py_enum.auto()))
                else:
                    members.append((k, v))

            base = new_class(_target_cls.__name__, (_target_cls, _BaseEnum), {})

            result = enum_class(_target_cls.__name__, members, type=base)  # type: ignore
            return cast(T_TargetEnum, result)

        if target_class:
            return wrap(target_class)
        return wrap
