from __future__ import annotations

from typing import Dict, Type, Any

import pydantic
from pydantic import main as pydantic_main
from pydantic.typing import resolve_annotations

from nodeedge import GlobalConfiguration

from ._base_model import BaseNodeModel, BaseLinkPropertyModel
from .fields import Field, nodeedge_field_info_from_field
from ._fields.field_types import UUID1
from ._fields.model_field import ModelField

__all__ = [
    "AbstractModel",
    "Model",
    "LinkPropertyModel",
]


class AbstractModel(pydantic_main.ModelMetaclass):
    def __new__(mcs, cls_name: str, bases, namespace, **kwargs):
        # noinspection PyTypeChecker
        model_class = super().__new__(mcs, cls_name, bases, namespace=namespace, **kwargs)

        hints: Dict[str, Type[Any]] = resolve_annotations(
            namespace.get("__annotations__", {}),
            namespace.get("__module__"),
        )

        for name, value in hints.items():
            _field: pydantic.fields.ModelField = model_class.__fields__[name]
            nodeedge_field_info = nodeedge_field_info_from_field(model_class, _field)
            field_params = create_field_params(name, _field)

            model_class.__fields__[name] = ModelField(
                nodeedge_field_info=nodeedge_field_info, **field_params
            )

        for k, f in model_class.__fields__.items():
            setattr(model_class, k, f)

        model_class.__hints__ = hints
        model_class.__annotations__ = hints
        return model_class


def create_field_params(name: str, _field: pydantic.fields.ModelField) -> Dict:
    field_type = _field.type_

    return {
        "type_": field_type,
        "class_validators": _field.class_validators,
        "model_config": _field.model_config,
        "default": _field.default,
        "default_factory": _field.default_factory,
        "final": _field.final,
        "alias": _field.alias,
        "field_info": _field.field_info,
        "name": name,
        "required": _field.required,
    }


if GlobalConfiguration.is_edgedb_backend():

    class Model(BaseNodeModel, metaclass=AbstractModel):
        id: UUID1 = Field(default=None, required=False)

else:

    class Model(BaseNodeModel, metaclass=AbstractModel):  # type: ignore[no-redef]
        pass


class LinkPropertyModel(BaseLinkPropertyModel, metaclass=AbstractModel):
    pass
