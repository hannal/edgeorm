from nodeedge.backends import BackendLoader
from nodeedge.backends.base import FieldTypeMap
from nodeedge.model import fields


def test_backend_loader(global_configuration):
    backend = BackendLoader(global_configuration.BACKEND)
    assert backend.namespace == global_configuration.BACKEND
    assert isinstance(backend.field_type_map, FieldTypeMap)

    field = fields.Str("hello world")
    assert isinstance(field._field_type_map, FieldTypeMap)
