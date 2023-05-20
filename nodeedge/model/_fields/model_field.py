from __future__ import annotations

from typing import Optional, Union, cast, Iterable

from typing_extensions import TYPE_CHECKING
from pydantic.fields import ModelField as _PydanticModelField
from pydantic.fields import FieldInfo as _PydanticFieldInfo

from nodeedge.types import FieldInfo
from .base_fields import NodeEdgeFieldInfo

if TYPE_CHECKING:
    pass


__all__ = ["ModelField"]


class ModelField(_PydanticModelField):
    def __init__(
        self,
        nodeedge_field_info: Optional[NodeEdgeFieldInfo] = None,
        **kwargs,
    ) -> None:
        field_info = substitute_field_info(
            origin=kwargs.pop("field_info", None),
            nodeedge=nodeedge_field_info,
        )
        super().__init__(field_info=field_info, **kwargs)


def substitute_field_info(
    origin: Union[_PydanticFieldInfo, None], nodeedge: Union[NodeEdgeFieldInfo, None]
) -> FieldInfo:
    field_info = FieldInfo(nodeedge=nodeedge)
    if origin:
        field_info.update_from_config(dict(cast(Iterable, origin.__repr_args__())))

    return field_info
