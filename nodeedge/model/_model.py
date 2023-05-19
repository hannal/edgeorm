from __future__ import annotations

from nodeedge import GlobalConfiguration

from ._base_model import AbstractModel

__all__ = [
    "Model",
    "LinkPropertyModel",
]

from ._base_model import BaseNodeModel, BaseLinkPropertyModel

if GlobalConfiguration.is_edgedb_backend():

    class Model(BaseNodeModel, metaclass=AbstractModel):
        pass

else:

    class Model(BaseNodeModel, metaclass=AbstractModel):
        pass


class LinkPropertyModel(BaseLinkPropertyModel, metaclass=AbstractModel):
    pass
