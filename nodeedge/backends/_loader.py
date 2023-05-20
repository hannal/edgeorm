from __future__ import annotations

from functools import cached_property
from importlib import import_module
from typing import Union

from nodeedge.backends.base import FieldTypeMap


__all__ = ["BackendLoader"]


class BaseBackendLoader(type):
    __instances: dict[str, BackendLoader] = {}

    def __call__(cls, namespace: str):
        if namespace not in cls.__instances:
            cls.__instances[namespace] = super().__call__(namespace)
        return cls.__instances[namespace]


class BackendLoader(metaclass=BaseBackendLoader):
    name: str
    package: str
    base_namespace: str
    _field_type_map: Union[FieldTypeMap, None]

    def __init__(self, backend: str):
        self.package, *back_namespace, self.name = backend.split(".")
        base_namespace = ".".join(back_namespace)
        self.base_namespace = f"{self.package}.{base_namespace}"
        self._field_type_map = None

    @cached_property
    def namespace(self):
        return f"{self.base_namespace}.{self.name}"

    @cached_property
    def field_type_map(self) -> FieldTypeMap:
        if not self._field_type_map:
            mod = import_module(self.namespace, package=self.package)
            self._field_type_map = mod.type_map
        return self._field_type_map
