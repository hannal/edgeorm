import pytest

from nodeedge import GlobalConfiguration

__all__ = [
    "skip_if_not_edgedb",
]

_is_backend_edgedb = GlobalConfiguration.is_edgedb_backend()

skip_if_not_edgedb = pytest.mark.skipif(not _is_backend_edgedb, reason="not edgedb backend")
