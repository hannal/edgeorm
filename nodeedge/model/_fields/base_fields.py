from __future__ import annotations

import dataclasses
import json
import uuid
from types import EllipsisType
from typing import TypeVar, Generic, Union, Type, Any, Sequence, cast

from typing_extensions import Self, TYPE_CHECKING, TypeAlias
from edgedb import Object as EdgeDBObject

from nodeedge import GlobalConfiguration
from nodeedge.backends import BackendLoader, FieldTypeMap
from nodeedge.model import BaseNodeModel, BaseLinkPropertyModel
from nodeedge.types import BaseFilterable, FieldInfo

__all__ = [
    "BaseField",
    "BaseListField",
    "BaseLinkField",
    "DBRawObject",
    "DBRawObjectType",
    "BaseUUIDField",
    "PythonValueFieldMixin",
    "DbValueFieldMixin",
    "PythonValueField_T",
    "DbValueField_T",
    "Link_T",
    "LinkProperty_T",
    "NodeEdgeFieldInfo",
]

if TYPE_CHECKING:
    Link_T = TypeVar("Link_T", bound=BaseNodeModel)
    LinkProperty_T = TypeVar("LinkProperty_T", bound=BaseLinkPropertyModel)
else:
    Link_T = TypeVar("Link_T", bound=BaseNodeModel)
    LinkProperty_T = TypeVar("LinkProperty_T", bound=BaseLinkPropertyModel)


_backend = BackendLoader(GlobalConfiguration.BACKEND)

if GlobalConfiguration.is_edgedb_backend():
    DBRawObject = EdgeDBObject
else:
    DBRawObject = EdgeDBObject

DBRawObjectType: TypeAlias = DBRawObject  # type: ignore

_field_type_map = _backend.field_type_map

PythonValueField_T = TypeVar("PythonValueField_T")


class PythonValueFieldMixin(Generic[PythonValueField_T]):
    _python_value: Union[PythonValueField_T, EllipsisType] = ...

    def as_python_value(self) -> Union[Self, PythonValueField_T]:
        if self._python_value is ...:
            return self
        return self._python_value


DbValueField_T = TypeVar("DbValueField_T")


class DbValueFieldMixin(Generic[DbValueField_T]):
    _db_value: Union[DbValueField_T, EllipsisType] = ...

    def as_db_value(self) -> Union[Self, DbValueField_T]:
        if self._db_value is ...:
            return self
        return self._db_value


class BaseField(BaseFilterable, PythonValueFieldMixin, DbValueFieldMixin):
    """Model을 정의할 때 사용하는 model field type의 base."""

    field_info: FieldInfo

    _field_type_map: FieldTypeMap = _field_type_map

    _db_link_type = None
    _db_field_type = None

    __allow_mixin_operation__ = False

    @classmethod
    def validate(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    @classmethod
    def get_validators(cls):
        for validator in cls.__get_validators__():
            yield validator

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def as_db_link_type(cls):
        return cls._db_link_type or cls.as_db_type()

    @classmethod
    def as_db_type(cls):
        return cls._db_field_type or getattr(cls._field_type_map, cls.__name__)

    def as_jsonable_value(self):
        if self._python_value is ...:
            raise ValueError(f"value is not set: {self}")
        return json.dumps(self.as_python_value())


Listable_T = TypeVar("Listable_T")


class BaseListField(Generic[Listable_T]):
    _data: Sequence[Listable_T]

    def __init__(self, value):
        self._data = value

    def __iter__(self):
        return self.data.__iter__()

    def __getattr__(self, name: str):
        return getattr(self.data, name)

    def __getitem__(self, key):
        return self.data[key]

    def __len__(self):
        return len(self.data)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.data.__repr__()})"

    @property
    def data(self):
        return self._data

    def as_jsonable_value(self):
        return [v.as_python_value() if hasattr(v, "as_python_value") else v for v in self.data]

    def as_db_value(self):
        return [v.as_db_value() if hasattr(v, "as_db_value") else v for v in self.data]


class BaseUUIDField(BaseField, PythonValueFieldMixin[uuid.UUID], DbValueFieldMixin[str]):
    @classmethod
    def validate(cls: Type, value: str | uuid.UUID):
        if isinstance(value, uuid.UUID):
            result = cls(value.hex)
        else:
            result = cls(value)

        return result

    def as_python_value(self):
        return self

    def as_db_value(self):
        return str(self.as_python_value())

    def as_jsonable_value(self):
        return self.as_db_value()


class BaseLinkField(DbValueFieldMixin, Generic[Link_T, LinkProperty_T]):
    __allow_mixin_operation__ = False

    @property
    def is_single_link(self) -> bool:
        raise NotImplementedError

    @property
    def is_multi_link(self) -> bool:
        raise NotImplementedError

    def __repr__(self):
        return f"{self.__class__.__name__})"

    def __getattr__(self, attr: str):
        data = self._db_value
        if hasattr(data, attr):
            return getattr(data, attr)

        return super().__getattribute__(attr)

    @classmethod
    def check_args(
        cls, value: Any
    ) -> Union[
        Self, BaseNodeModel, uuid.UUID, tuple[BaseNodeModel, Union[BaseLinkPropertyModel, None]]
    ]:
        if isinstance(value, cls):
            return value
        elif isinstance(value, BaseNodeModel):
            return value
        elif isinstance(value, uuid.UUID):
            return value
        elif isinstance(value, DBRawObject):
            return value.id
        elif isinstance(value, (tuple, list)):
            link_data, link_property = value
            if isinstance(link_data, BaseNodeModel) and (
                not link_property or isinstance(link_property, BaseLinkPropertyModel)
            ):
                return cast(tuple[BaseNodeModel, Union[BaseLinkPropertyModel, None]], value)

        raise ValueError(f"invalid Link value type: {type(value)}")

    def as_jsonable_value(self):
        return json.dumps(self.as_db_value())


@dataclasses.dataclass(frozen=True, kw_only=True)
class NodeEdgeFieldInfo:
    model: Type[BaseNodeModel]
    deferred: bool
    is_single_link: bool = dataclasses.field(default=False)
    is_multi_link: bool = dataclasses.field(default=False)
    link_model: Union[Type[BaseNodeModel], None] = dataclasses.field(default=None)
    link_property_model: Union[Type[BaseLinkPropertyModel], None] = dataclasses.field(default=None)

    @property
    def is_link(self):
        return self.is_single_link or self.is_multi_link
