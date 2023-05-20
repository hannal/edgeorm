from __future__ import annotations

from typing import Any

import pydantic
from pydantic.typing import update_model_forward_refs

__all__ = ["BaseModel", "BaseNodeModel", "BaseLinkPropertyModel", "Config"]


class Config(pydantic.BaseConfig):
    # pydantic configurations
    orm_mode = True
    is_model_field_value_type_fields = False

    # nodeedge configurations
    node_name = ""


class BaseModel(pydantic.BaseModel):
    __config__ = Config

    @classmethod
    def update_forward_refs(cls, **localns: Any) -> None:
        update_model_forward_refs(
            cls,
            cls.__fields__.values(),
            cls.__config__.json_encoders,
            localns,
        )

    @classmethod
    def from_orm(cls, obj: Any):
        return super().from_orm(obj)


class BaseNodeModel(BaseModel):
    @classmethod
    def get_node_name(cls) -> str:
        if not cls.__config__.node_name:
            raise ValueError(f"required Config.node_name of model: {cls.__name__}")
        return cls.__config__.node_name


class BaseLinkPropertyModel(BaseModel):
    pass
