import pytest

from nodeedge import GlobalConfiguration
from nodeedge.model import fields, Model, LinkPropertyModel

is_backend_edgedb = GlobalConfiguration.is_edgedb_backend()

skip_if_not_edgedb = pytest.mark.skipif(not is_backend_edgedb, reason="not edgedb backend")


class TargetModel(Model):
    name: fields.Str


class TargetLinkProperty(LinkPropertyModel):
    value: fields.Int16


class SampleModel(Model):
    name: fields.Str
    link: fields.Link[TargetModel, None]
    prop: fields.Link[TargetModel, TargetLinkProperty]


class MultiLinkModel(Model):
    hello: fields.Str
    links: fields.MultiLink[TargetModel, None]
    props: fields.MultiLink[TargetModel, TargetLinkProperty]


@skip_if_not_edgedb
def test_single_link():
    target = TargetModel(name="hello")
    target2 = TargetModel(name="world")
    target2_prop = TargetLinkProperty(value=1)

    model = SampleModel(name="world", link=target, prop=[target2, target2_prop])

    assert model.link.is_single_link
    assert model.prop.is_single_link
    assert hasattr(model.link, "name")
    assert model.link.get_link_data() == target

    assert model.prop.get_link_data() == target2
    assert model.prop.get_link_property() == target2_prop


@skip_if_not_edgedb
def test_multi_link():
    target = TargetModel(name="hello")
    target_prop = TargetLinkProperty(value=4)
    target2 = TargetModel(name="world")
    target2_prop = TargetLinkProperty(value=2)

    model = MultiLinkModel(
        hello="world",
        links=[target, target2],
        props=[[target, target_prop], [target2, target2_prop]],
    )

    assert model.links.is_multi_link
    assert len(model.links) == 2
    assert model.props.is_multi_link
    assert len(model.props) == 2

    link_item1, link_item2 = model.links
    assert link_item1.get_link_data() == target
    assert link_item2.get_link_data() == target2

    prop_item1, prop_item2 = model.props
    assert prop_item1.get_link_data() == target
    assert prop_item1.get_link_property() == target_prop
    assert prop_item2.get_link_data() == target2
    assert prop_item2.get_link_property() == target2_prop
