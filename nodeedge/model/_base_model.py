from __future__ import annotations

from typing import Dict, Type, Any

import pydantic
from pydantic import main as pydantic_main
from pydantic.typing import resolve_annotations, update_model_forward_refs

from ._fields.model_field import ModelField  # noqa


__all__ = ["AbstractModel", "BaseModel", "BaseNodeModel", "BaseLinkPropertyModel", "Config"]


class AbstractModel(pydantic_main.ModelMetaclass):
    def __new__(mcs, cls_name: str, bases, namespace, **kwargs):
        # noinspection PyTypeChecker
        model_class = super().__new__(mcs, cls_name, bases, namespace=namespace, **kwargs)

        hints: Dict[str, Type[Any]] = resolve_annotations(
            namespace.get("__annotations__", {}),
            namespace.get("__module__"),
        )

        model_class.__hints__ = hints
        model_class.__annotations__ = hints

        for name, value in hints.items():
            field: pydantic.fields.ModelField = model_class.__fields__[name]

            field_type = field.annotation

            field_params = {
                "type_": field_type,
                "class_validators": field.class_validators,
                "model_config": field.model_config,
                "default": field.default,
                "default_factory": field.default_factory,
                "final": field.final,
                "alias": field.alias,
                "field_info": field.field_info,
                "name": name,
                "required": field.required,
            }

            model_class.__fields__[name] = ModelField(**field_params)

        for k, f in model_class.__fields__.items():
            setattr(model_class, k, f)

        return model_class


class Config(pydantic.BaseConfig):
    # pydantic configurations
    orm_model = True
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
        if not cls.Config.node_name:
            raise ValueError(f"required Config.node_name of model: {cls.__name__}")
        return cls.Config.node_name


class BaseLinkPropertyModel(BaseModel):
    pass
