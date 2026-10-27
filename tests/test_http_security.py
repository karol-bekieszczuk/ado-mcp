from contextlib import asynccontextmanager

import httpx2 as httpx
import pytest

from ado_mcp import server

INITIALIZE = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {},
        "clientInfo": {"name": "pytest", "version": "0"},
    },
}
ACCEPT = {"Accept": "application/json, text/event-stream"}


@asynccontextmanager
async def http_client():
    app = server.create_server().http_app(**server.HTTP_SECURITY)
    async with (
        app.router.lifespan_context(app),
        httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url="http://127.0.0.1:8000",
        ) as c,
    ):
        yield c


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        pytest.param({}, 200, id="no-origin-allowed"),
        pytest.param(
            {"Origin": "http://localhost:8000"}, 200, id="local-origin-allowed"
        ),
        pytest.param(
            {"Origin": "http://evil.example"}, 403, id="foreign-origin-rejected"
        ),
        pytest.param({"Origin": "null"}, 403, id="null-origin-rejected"),
        pytest.param({"Host": "evil.example:8000"}, 421, id="foreign-host-rejected"),
    ],
)
async def test_host_and_origin_validation(headers, expected_status):
    async with http_client() as client:
        response = await client.post(
            "/mcp", json=INITIALIZE, headers={**ACCEPT, **headers}
        )
    assert response.status_code == expected_status
