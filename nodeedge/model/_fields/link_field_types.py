from __future__ import annotations

import uuid
from functools import lru_cache
from typing import List, Any, Union, cast, Optional

from pydantic.validators import list_validator
from typing_extensions import Self, TypeAlias

from .._base_model import BaseNodeModel, BaseLinkPropertyModel
from .base_fields import (
    BaseField,
    BaseListField,
    BaseLinkField,
    Link_T,
    LinkProperty_T,
    DBRawObject,
)


__all__ = [
    "Link",
    "MultiLink",
    "LinkDataType",
    "LinkPropertyDataType",
]


LinkDataType: TypeAlias = Union[BaseNodeModel, uuid.UUID, DBRawObject]
LinkPropertyDataType: TypeAlias = Union[BaseLinkPropertyModel, None]


class Link(BaseLinkField[Link_T, LinkProperty_T], BaseField):
    _db_value: Union[Link_T, uuid.UUID]
    _link_property: Union[LinkProperty_T, None]

    def __init__(
        self,
        link_data: Union[Link_T, uuid.UUID],
        link_property: Optional[LinkProperty_T] = None,
    ):
        self._db_value = link_data
        self._link_property = link_property

    @property
    def is_single_link(self) -> bool:
        return True

    @property
    def is_multi_link(self) -> bool:
        return False

    @property
    def is_id_link(self):
        return isinstance(self._db_value, uuid.UUID)

    @lru_cache
    def get_link_data(self) -> Link_T | uuid.UUID:
        return self._db_value

    @lru_cache
    def get_link_property(self) -> LinkProperty_T | None:
        return self._link_property

    @classmethod
    def __get_validators__(cls):
        yield cls.check_args
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Self:
        link_data: Union[BaseNodeModel, uuid.UUID, DBRawObject]
        link_property: Optional[BaseLinkPropertyModel] = None
        if isinstance(value, (list, tuple)):
            if len(value) != 2:
                raise ValueError(
                    "invalid Link value: must be a tuple of (link_data, link_property)"
                )

            link_data, link_property = value
        else:
            link_data = value

        if not isinstance(link_data, (BaseNodeModel, uuid.UUID, DBRawObject)):
            raise ValueError(f"invalid Link value type: {type(link_data)}")

        if link_property and not isinstance(link_property, BaseLinkPropertyModel):
            raise ValueError(f"invalid LinkProperty value type: {type(link_property)}")

        result = cls(cast(Link_T, link_data), cast(LinkProperty_T, link_property))
        return result


class MultiLink(
    BaseLinkField[Link_T, LinkProperty_T],
    BaseListField[List, Link[Link_T, LinkProperty_T]],
    BaseField,
):
    _db_value: List[Link[Link_T, LinkProperty_T]]

    def __init__(self, value: List):
        _db_value = [Link.validate(v) for v in value]
        self._db_value = _db_value
        super().__init__(_db_value)

    @property
    def is_single_link(self) -> bool:
        return False

    @property
    def is_multi_link(self) -> bool:
        return True

    @classmethod
    def __get_validators__(cls):
        yield list_validator
        yield cls.validate_each
        yield cls.validate

    @classmethod
    def validate_each(cls, value: Any):
        for item in value:
            Link.check_args(item)
        return value

    @classmethod
    def validate(cls, value: Any) -> Self:
        if isinstance(value, cls):
            return value
        return cls(value)
