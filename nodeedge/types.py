from __future__ import annotations

from collections import OrderedDict
from typing import Mapping, Type, Dict, Any, Optional, Iterable, TypeVar, Iterator


__all__ = ["BaseFilterable", "ImmutableDict", "ValueClass"]


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
    def fromkeys(cls, seq: Iterable[_KT], value: Optional[_KV] = None) -> "immutabledict[_KT, _KV]":
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
        raise TypeError("GlobalVariables cannot be instantiated")
