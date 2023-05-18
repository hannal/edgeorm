import os
import asyncio
import sys

import pytest

from nodeedge import GlobalConfiguration


@pytest.fixture(autouse=True)
def global_configuration(monkeypatch):
    backend = os.environ.get("NODEEDGE_BACKEND", "nodeedge.backends.edgedb")
    with monkeypatch.context() as ctx:
        ctx.setattr(GlobalConfiguration, "BACKEND", backend)
        yield GlobalConfiguration


@pytest.fixture(scope="session", autouse=True)
def event_loop():
    if sys.platform.startswith("win") and sys.version_info[:2] >= (3, 8):
        # Avoid "RuntimeError: Event loop is closed" on Windows when tearing down tests
        # https://github.com/encode/httpx/issues/914
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop


def pytest_sessionfinish(session, exitstatus):
    try:
        asyncio.get_event_loop().close()
    except RuntimeError as e:
        import warnings

        warnings.warn(str(e))
        warnings.warn(str(exitstatus))
