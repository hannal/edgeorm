from __future__ import annotations

import json
import uuid
import dataclasses
from types import EllipsisType
from typing import TypeVar, Generic, Union, Type, Any, Optional, overload
from typing_extensions import Self, TYPE_CHECKING
from edgedb import Object as EdgeDBObject
from pydantic.fields import Field as _PydanticField, FieldInfo as _PydanticFieldInfo

from nodeedge import GlobalConfiguration, Undefined
from nodeedge.backends import BackendLoader
from nodeedge.backends.base import FieldTypeMap
from nodeedge.model._base_model import BaseNodeModel, BaseLinkPropertyModel
from nodeedge.types import BaseFilterable, FieldInfo
from ...utils.typing import annotate_from


__all__ = [
    "field",
    "NodeEdgeFieldInfo",
    "BaseField",
    "BaseListField",
    "BaseLinkField",
    "DBRawObject",
    "BaseUUIDField",
    "PythonValueFieldMixin",
    "DbValueFieldMixin",
    "PythonValueField_T",
    "DbValueField_T",
    "Link_T",
    "LinkProperty_T",
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

_field_type_map = _backend.field_type_map

PythonValueField_T = TypeVar("PythonValueField_T")


class PythonValueFieldMixin(Generic[PythonValueField_T]):
    _python_value: Union[PythonValueField_T, EllipsisType] = ...

    def as_python_value(self) -> PythonValueField_T:
        if self._python_value is ...:
            return self
        return self._python_value


DbValueField_T = TypeVar("DbValueField_T")


class DbValueFieldMixin(Generic[DbValueField_T]):
    _db_value: Union[DbValueField_T, EllipsisType] = ...

    def as_db_value(self) -> DbValueField_T:
        if self._db_value is ...:
            return self
        return self._db_value


class BaseField(BaseFilterable, PythonValueFieldMixin, DbValueFieldMixin):
    """Model을 정의할 때 사용하는 model field type의 base."""

    field_info: FieldInfo

    _backend: str = _backend
    _field_type_map: FieldTypeMap = _field_type_map

    _db_link_type = None
    _db_field_type = None

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
Container_T = TypeVar("Container_T")


class BaseListField(Generic[Container_T, Listable_T]):
    _data: Container_T[Listable_T]

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
    def validate(cls: Type[uuid.UUID], value: str | uuid.UUID):
        if isinstance(value, uuid.UUID):
            result = cls(value.hex)
        else:
            result = cls(value)

        return result

    def as_python_value(self) -> PythonValueField_T:
        return self

    def as_db_value(self) -> DbValueField_T:
        return str(self.as_python_value())

    def as_jsonable_value(self):
        return self.as_db_value()


class BaseLinkField(DbValueFieldMixin, Generic[Link_T, LinkProperty_T]):
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
                return value

        raise ValueError(f"invalid Link value type: {type(value)}")

    def as_jsonable_value(self):
        return json.dumps(self.as_db_value())


@dataclasses.dataclass(frozen=True, kw_only=True)
class NodeEdgeFieldInfo:
    model: Type[BaseNodeModel]
    link_property_model: Optional[Type[BaseLinkPropertyModel]] = dataclasses.field(default=None)

    @property
    def is_single_link(self):
        return False

    @property
    def is_multi_link(self):
        return False


@annotate_from(_PydanticField)
def field(
    default: Any = Undefined,
    *,
    # for nodeedge
    model: Optional[Type[BaseNodeModel]] = None,
    # for pydantic
    **kwargs,
) -> FieldInfo:
    nodeedge = None

    if model:
        nodeedge = NodeEdgeFieldInfo(
            model=model,
        )

    field_info = FieldInfo(default, nodeedge=nodeedge, **kwargs)
    field_info._validate()
    return field_info
