import abc
import inspect
from typing import FrozenSet, Tuple, Optional, Dict, Union, List, Set

from typing_extensions import Self


__all__ = [
    "Cloneable",
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
            if param.kind in [param.POSITIONAL_ONLY, param.VAR_POSITIONAL]:
                init_args.append(name)
            elif param.kind in [param.VAR_KEYWORD, param.POSITIONAL_OR_KEYWORD, param.KEYWORD_ONLY]:
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
