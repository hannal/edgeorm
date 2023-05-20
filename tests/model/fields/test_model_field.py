import pydantic

from nodeedge.model import fields, Model
from nodeedge.model.fields import NodeEdgeFieldInfo
from nodeedge.types import FieldInfo
from _testing.decorators import skip_if_not_edgedb


class SampleModel(Model):
    hello: fields.Str


class NotNodedgeModel(pydantic.BaseModel):
    world: fields.Str


@skip_if_not_edgedb
def test_model_field_has_nodeedge_own_field_info():
    field = SampleModel.hello

    # field info for nodeedge model
    assert isinstance(field.field_info, FieldInfo)
    assert hasattr(field.field_info, "nodeedge")
    assert isinstance(field.field_info.nodeedge, NodeEdgeFieldInfo)

    # field info for non-nodeedge model
    field = NotNodedgeModel.__fields__["world"]
    assert isinstance(field.field_info, pydantic.fields.FieldInfo)
    assert not hasattr(field.field_info, "nodeedge")
