import pydantic

from nodeedge.model import fields, Model, LinkPropertyModel
from nodeedge.model.fields import NodeEdgeFieldInfo
from nodeedge.types import FieldInfo
from _testing.decorators import skip_if_not_edgedb


@skip_if_not_edgedb
def test_model_field_has_nodeedge_own_field_info():
    class SampleModel(Model):
        hello: fields.Str

    class NotNodedgeModel(pydantic.BaseModel):
        world: fields.Str

    field = SampleModel.hello

    # field info for nodeedge model
    assert isinstance(field.field_info, FieldInfo)
    assert hasattr(field.field_info, "nodeedge")
    assert isinstance(field.field_info.nodeedge, NodeEdgeFieldInfo)
    assert field.field_info.nodeedge.model is SampleModel

    # field info for non-nodeedge model
    field = NotNodedgeModel.__fields__["world"]
    assert isinstance(field.field_info, pydantic.fields.FieldInfo)
    assert not hasattr(field.field_info, "nodeedge")


def test_link_fields():
    class LinkProperty(LinkPropertyModel):
        prop: fields.Str

    class Target(Model):
        target: fields.Int16

    class SampleModel(Model):
        single: fields.Link[Target, None]
        single2: fields.Link[Target, LinkProperty]
        multi: fields.MultiLink[Target, None]
        multi2: fields.MultiLink[Target, LinkProperty]

    nodeedge: NodeEdgeFieldInfo
    for _f, _is_single, _is_multi, _link_prop in [
        [SampleModel.single, True, False, None],
        [SampleModel.single2, True, False, LinkProperty],
        [SampleModel.multi, False, True, None],
        [SampleModel.multi2, False, True, LinkProperty],
    ]:
        nodeedge = _f.field_info.nodeedge
        assert nodeedge.model is SampleModel
        assert nodeedge.is_single_link is _is_single
        assert nodeedge.is_multi_link is _is_multi
        assert nodeedge.link_model is Target
        assert nodeedge.link_property_model is _link_prop
