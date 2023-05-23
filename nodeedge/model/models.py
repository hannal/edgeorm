from __future__ import annotations

import inspect
from collections import defaultdict
from typing import Dict, Type, Any

import pydantic
from pydantic import main as pydantic_main
from pydantic.typing import resolve_annotations

from nodeedge import GlobalConfiguration
from nodeedge.mixins import Cloneable


from ._base_model import BaseNodeModel, BaseLinkPropertyModel
from .fields import field, nodeedge_field_info_from_field, Field
from ._fields.field_types import UUID1

__all__ = [
    "AbstractModel",
    "Model",
    "LinkPropertyModel",
]

from ..types import FieldInfo

from ..utils.typing import sort_function_parameters


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
            field_params["field_info"] = FieldInfo(nodeedge=nodeedge_field_info)

            model_class.__fields__[name] = Field(**field_params)

        for k, f in model_class.__fields__.items():
            setattr(model_class, k, f)

        model_class.__hints__ = hints
        model_class.__annotations__ = hints

        sig = inspect.signature(model_class.__init__)

        init_params: dict = defaultdict(list)

        init_params[inspect.Parameter.KEYWORD_ONLY] = [
            inspect.Parameter(
                name=_name,
                annotation=_field.annotation,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=_field.field_info,
            )
            for _name, _field in model_class.__fields__.items()
            if _name not in sig.parameters
        ]
        for param in sig.parameters.values():
            init_params[param.kind].append(param)

        model_class.__init__.__signature__ = sig.replace(
            parameters=sort_function_parameters(init_params),
        )

        for _mro in model_class.__mro__:
            if not getattr(_mro, "__is_mixin__", False):
                continue
            for k, v in _mro.__dict__.items():
                if k.startswith("__"):
                    continue
                setattr(model_class, k, v)

            # if Cloneable in model_class.__mro__:
            if _mro is Cloneable:
                model_class.__init_kwargs__ = frozenset(model_class.__fields__.keys())
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
        id: UUID1 = field(default=None, required=False)

else:

    class Model(BaseNodeModel, metaclass=AbstractModel):  # type: ignore[no-redef]
        pass


class LinkPropertyModel(BaseLinkPropertyModel, metaclass=AbstractModel):
    pass
