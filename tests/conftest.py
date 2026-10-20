import asyncio
from pathlib import Path
import sys

import pytest
from httpx import ASGITransport, AsyncClient


REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class ASGITestClient:
    """通过 HTTPX ASGI 传输层同步调用应用，避免依赖 TestClient 适配层。"""

    def __init__(self, app, host="127.0.0.1"):
        self.app = app
        self.host = host

    def request(self, method, path, **kwargs):
        async def send_request():
            transport = ASGITransport(
                app=self.app,
                client=(self.host, 50000),
            )
            async with AsyncClient(
                transport=transport,
                base_url="http://testserver",
            ) as client:
                return await client.request(method, path, **kwargs)

        return asyncio.run(send_request())

    def get(self, path, **kwargs):
        return self.request("GET", path, **kwargs)

    def post(self, path, **kwargs):
        return self.request("POST", path, **kwargs)

    def put(self, path, **kwargs):
        return self.request("PUT", path, **kwargs)

    def options(self, path, **kwargs):
        return self.request("OPTIONS", path, **kwargs)


@pytest.fixture
def asgi_client_factory():
    return ASGITestClient
