from __future__ import annotations

from nodeedge import GlobalConfiguration

from .fields import UUID1, Field
from ._base_model import AbstractModel

__all__ = [
    "Model",
    "LinkPropertyModel",
]

from ._base_model import BaseNodeModel, BaseLinkPropertyModel

if GlobalConfiguration.is_edgedb_backend():

    class Model(BaseNodeModel, metaclass=AbstractModel):
        id: UUID1 = Field(default=None, required=False)

else:

    class Model(BaseNodeModel, metaclass=AbstractModel):
        pass


class LinkPropertyModel(BaseLinkPropertyModel, metaclass=AbstractModel):
    pass
