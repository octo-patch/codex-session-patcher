import asyncio
from types import SimpleNamespace

from starlette.websockets import WebSocketDisconnect

from web.backend.api import websocket_endpoint
from web.backend.main import app


class FakeWebSocket:
    def __init__(self, host="127.0.0.1", origin=None):
        self.client = SimpleNamespace(host=host)
        self.headers = {} if origin is None else {"origin": origin}
        self.accepted = False
        self.close_code = None

    async def accept(self):
        self.accepted = True

    async def close(self, code, reason=None):
        self.close_code = code

    async def receive_text(self):
        raise WebSocketDisconnect()


def test_http_allows_loopback_client_without_origin(asgi_client_factory):
    response = asgi_client_factory(app).get("/api/version")

    assert response.status_code == 200


def test_http_rejects_non_loopback_client(asgi_client_factory):
    response = asgi_client_factory(app, "192.168.2.50").get("/api/version")

    assert response.status_code == 403
    assert response.json() == {"detail": "仅允许本机访问"}


def test_http_rejects_non_local_origin(asgi_client_factory):
    response = asgi_client_factory(app).put(
        "/api/settings",
        headers={"Origin": "https://attacker.example"},
        json={},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "不允许的请求来源"}


def test_cors_allows_local_origin(asgi_client_factory):
    response = asgi_client_factory(app).options(
        "/api/settings",
        headers={
            "Origin": "http://localhost:47832",
            "Access-Control-Request-Method": "PUT",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:47832"


def test_cors_accepts_case_insensitive_localhost(asgi_client_factory):
    response = asgi_client_factory(app).options(
        "/api/settings",
        headers={
            "Origin": "http://LOCALHOST:47832",
            "Access-Control-Request-Method": "PUT",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://LOCALHOST:47832"


def test_websocket_rejects_non_local_origin():
    websocket = FakeWebSocket(origin="https://attacker.example")

    asyncio.run(websocket_endpoint(websocket))

    assert websocket.accepted is False
    assert websocket.close_code == 1008


def test_websocket_accepts_loopback_without_origin():
    websocket = FakeWebSocket()

    asyncio.run(websocket_endpoint(websocket))

    assert websocket.accepted is True
    assert websocket.close_code is None
