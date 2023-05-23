from __future__ import annotations

from typing import Any, Type, ForwardRef, Union, cast, Iterable

import pydantic
from pydantic import Field as _PydanticField
from pydantic.fields import (
    Undefined,
    ModelField as _PydanticModelField,
    FieldInfo as _PydanticFieldInfo,
)
from pydantic.utils import smart_deepcopy

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
from ..exceptions import InvalidPathError
from ..mixins import Pathable, Valueable, Cloneable, _CloningAttrsType
from ..types import FieldInfo, PathDirectionType
from ..utils.typing import annotate_from, get_args, is_subclass


__all__ = [
    #
    # .
    "field",
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
]


@annotate_from(_PydanticField)
def field(default: Any = Undefined, **kwargs) -> FieldInfo:
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


class Field(_PydanticModelField, Pathable, Valueable, Cloneable):
    field_info: FieldInfo

    __cloning_operator__ = staticmethod(smart_deepcopy)
    __cloning_attrs__: _CloningAttrsType = frozenset(["field_info"])

    def __init__(self, **kwargs) -> None:
        origin_field_info = kwargs.pop("field_info", None)
        if isinstance(origin_field_info, FieldInfo):
            field_info = origin_field_info
        elif isinstance(origin_field_info, NodeEdgeFieldInfo):
            field_info = self.substitute_field_info(
                origin=None,
                nodeedge=origin_field_info,
            )
        else:
            field_info = self.substitute_field_info(
                origin=origin_field_info,
                nodeedge=None,
            )

        super().__init__(field_info=field_info, **kwargs)

    def __eq__(self, other: Any):
        if not isinstance(other, Field):
            return False

        assert isinstance(other, Field)

        result = self.type_ == other.type_

        if self.field_info.nodeedge and other.field_info.nodeedge:
            assert self.field_info.nodeedge is not None
            assert other.field_info.nodeedge is not None
            result &= self.field_info.nodeedge.model == other.field_info.nodeedge.model

        result &= self.name == other.name
        result &= self.value == other.value
        return result

    @staticmethod
    def substitute_field_info(
        origin: Union[_PydanticFieldInfo, None], nodeedge: Union[NodeEdgeFieldInfo, None]
    ) -> FieldInfo:
        field_info = FieldInfo(nodeedge=nodeedge)
        if origin:
            field_info.update_from_config(dict(cast(Iterable, origin.__repr_args__())))

        return field_info

    @classmethod
    def check_pathable(cls, other: Any, direction: PathDirectionType) -> Pathable:
        other = super().check_pathable(other, direction)
        if direction == "forward" and isinstance(other, BaseNodeModel):
            raise InvalidPathError(
                f"Cannot create path from {cls.__name__} to {other.__class__.__name__}"
            )
        return other
