from __future__ import annotations

from collections import OrderedDict
from typing import Mapping, Type, Dict, Any, Optional, Iterable, TypeVar, Iterator, Union

from typing_extensions import TYPE_CHECKING
from pydantic.fields import UndefinedType
from pydantic.fields import FieldInfo as _PydanticFieldInfo

from .constants import Undefined

if TYPE_CHECKING:
    from .model import BaseNodeModel
    from .model.fields import NodeEdgeFieldInfo


__all__ = ["BaseFilterable", "ImmutableDict", "ValueClass", "UndefinedType", "FieldInfo"]


class BaseFilterable:
    pass


_KT = TypeVar("_KT")
_KV = TypeVar("_KV")


class ImmutableDict(Mapping[_KT, _KV]):
    _dict_cls: Type[Dict[Any, Any]]

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

    def copy(self, **kwargs: _KV) -> ImmutableDict[_KT, _KV]:
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
        for key, value in self.items():
            value ^= hash((key, value))
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
