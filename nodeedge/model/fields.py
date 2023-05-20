from __future__ import annotations

from typing import Any, Type, ForwardRef, Union, cast

import pydantic
from pydantic import Field as _PydanticField
from pydantic.fields import Undefined

from nodeedge.utils import logger
from . import BaseNodeModel, BaseLinkPropertyModel
from ._fields.base_fields import (
    BaseField,
    BaseListField,
    BaseUUIDField,
    BaseLinkField,
    NodeEdgeFieldInfo,
)
from ._fields.field_types import (
    Str,
    Int16,
    Int32,
    Int64,
    BigInt,
    Float32,
    Float64,
    Decimal,
    Bool,
    Date,
    Time,
    NaiveDateTime,
    AwareDateTime,
    Duration,
    RelativeDuration,
    DateDuration,
    Json,
    UUID1,
    UUID3,
    UUID4,
    UUID5,
    Bytes,
    Array,
    Set,
    Tuple,
    NamedTuple,
)
from ._fields.link_field_types import Link, MultiLink
from ._fields.model_field import ModelField
from ..types import FieldInfo
from ..utils.typing import annotate_from, get_args, is_subclass

__all__ = [
    #
    # .
    "Field",
    "nodeedge_field_info_from_field",
    #
    # ._fields.base_fields
    "BaseField",
    "BaseUUIDField",
    "BaseListField",
    "BaseLinkField",
    "NodeEdgeFieldInfo",
    #
    # _field_types
    "Str",
    "Int16",
    "Int32",
    "Int64",
    "BigInt",
    "Float32",
    "Float64",
    "Decimal",
    "Bool",
    "Date",
    "Time",
    "NaiveDateTime",
    "AwareDateTime",
    "Duration",
    "RelativeDuration",
    "DateDuration",
    "Json",
    "UUID1",
    "UUID3",
    "UUID4",
    "UUID5",
    "Bytes",
    "Array",
    "Set",
    "Tuple",
    "NamedTuple",
    #
    # _link_field_types
    "Link",
    "MultiLink",
    #
    # _model_field
    "ModelField",
]


@annotate_from(_PydanticField)
def Field(default: Any = Undefined, **kwargs) -> FieldInfo:
    field_info = FieldInfo(default, **kwargs)
    field_info._validate()
    return field_info


def nodeedge_field_info_from_field(model: Type[BaseNodeModel], _field: pydantic.fields.ModelField):
    if isinstance(_field.type_, ForwardRef):
        return NodeEdgeFieldInfo(
            model=model,
            deferred=True,
        )

    field_type = _field.type_
    field_annotation = _field.annotation
    is_single_link = is_multi_link = False
    link_model: Union[Type[BaseNodeModel], None] = None
    link_property_model: Union[Type[BaseLinkPropertyModel], None] = None

    field_type = cast(Type, field_type)
    if is_subclass(field_type, BaseLinkField):
        is_single_link = is_subclass(field_type, Link)
        is_multi_link = is_subclass(field_type, MultiLink)

        link_model, link_property_model, *_ = get_args(field_annotation)

        if not is_subclass(link_model, BaseNodeModel):
            logger.warning("Link model is not a subclass of BaseNodeModel")
            link_model = None
        if not is_subclass(link_property_model, BaseLinkPropertyModel):
            logger.warning("Link property model is not a subclass of BaseLinkPropertyModel")
            link_property_model = None

    return NodeEdgeFieldInfo(
        model=model,
        deferred=False,
        is_single_link=is_single_link,
        is_multi_link=is_multi_link,
        link_model=link_model,
        link_property_model=link_property_model,
    )
