from __future__ import annotations

from typing import Any

import pydantic
from pydantic.typing import update_model_forward_refs

from nodeedge.mixins import Cloneable, Pathable

__all__ = ["BaseModel", "BaseNodeModel", "BaseLinkPropertyModel", "Config"]


class Config(pydantic.BaseConfig):
    # pydantic configurations
    orm_mode = True
    is_model_field_value_type_fields = False

    # nodeedge configurations
    node_name = ""


class BaseModel(pydantic.BaseModel):
    __config__ = Config

    def __setattr__(self, name, value):
        if name not in self.__fields__:
            # prevent pydantic from setting attribute as a model field
            object.__setattr__(self, name, value)
        else:
            super().__setattr__(name, value)

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


class BaseNodeModel(Pathable, Cloneable, BaseModel):
    @classmethod
    def get_node_name(cls) -> str:
        if not cls.__config__.node_name:
            raise ValueError(f"required Config.node_name of model: {cls.__name__}")
        return cls.__config__.node_name

    def __rshift__(self, other):
        raise TypeError(f"{self.__class__.__name__} cannot be a right operand of '>>' operator")

    def __lshift__(self, other):
        raise


class BaseLinkPropertyModel(BaseModel):
    pass
