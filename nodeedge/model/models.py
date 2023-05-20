from __future__ import annotations

from typing import Dict, Type, Any, ForwardRef

import pydantic
from pydantic import main as pydantic_main
from pydantic.typing import resolve_annotations

from nodeedge import GlobalConfiguration

from ._fields.base_fields import field
from ._fields.field_types import UUID1
from ._fields.link_field_types import Link, MultiLink

__all__ = [
    "AbstractModel",
    "Model",
    "LinkPropertyModel",
]

from ._base_model import BaseModel, BaseNodeModel, BaseLinkPropertyModel
from ._fields.model_field import ModelField
from ..utils.typing import is_class


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

            field_params = create_field_params(name, _field, model_class)

            model_class.__fields__[name] = ModelField(**field_params)

        for k, f in model_class.__fields__.items():
            setattr(model_class, k, f)

        model_class.__hints__ = hints
        model_class.__annotations__ = hints
        return model_class


def create_field_params(
    name: str, _field: pydantic.fields.ModelField, model_class: Type[BaseModel]
) -> Dict:
    field_type = _field.type_


    if isinstance(field_type, ForwardRef):
        pass
    elif is_class(field_type):
        issubclass(field_type, Link)
        issubclass(field_type, MultiLink)

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
        # nodeedge
        "model": model_class,
    }


if GlobalConfiguration.is_edgedb_backend():

    class Model(BaseNodeModel, metaclass=AbstractModel):
        id: UUID1 = field(default=None, required=False)

else:

    class Model(BaseNodeModel, metaclass=AbstractModel):
        pass


class LinkPropertyModel(BaseLinkPropertyModel, metaclass=AbstractModel):
    pass
