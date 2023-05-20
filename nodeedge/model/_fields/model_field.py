from __future__ import annotations

from typing import Type, Any, Optional, Dict, Union

from typing_extensions import Self, TYPE_CHECKING
from pydantic.fields import ModelField as _PydanticModelField
from pydantic.fields import FieldInfo as _PydanticFieldInfo

from nodeedge.types import FieldInfo
from .base_fields import NodeEdgeFieldInfo

if TYPE_CHECKING:
    from .._base_model import BaseNodeModel, BaseLinkPropertyModel


__all__ = ["ModelField"]


class ModelField(_PydanticModelField):
    def __init__(
        self,
        model: Optional[Type[BaseNodeModel]] = None,
        link_property_model: Optional[Type[BaseLinkPropertyModel]] = None,
        **kwargs,
    ) -> None:
        field_info = substitute_field_info(
            kwargs.pop("field_info", None),
            create_nodeedge_field_info(model, link_property_model),
        )
        super().__init__(field_info=field_info, **kwargs)


def create_nodeedge_field_info(
    model: Optional[Type[BaseNodeModel]] = None,
    link_property_model: Optional[Type[BaseLinkPropertyModel]] = None,
) -> Union[NodeEdgeFieldInfo, None]:
    if not model:
        return None

    return NodeEdgeFieldInfo(
        model=model,
        link_property_model=link_property_model,
    )


def substitute_field_info(
    origin: Union[_PydanticFieldInfo, None], nodeedge: Union[NodeEdgeFieldInfo, None]
) -> FieldInfo:
    field_info = FieldInfo(nodeedge=nodeedge)
    if origin:
        field_info.update_from_config(dict(origin.__repr_args__()))

    return field_info
