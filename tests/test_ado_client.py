import base64

import httpx2
import pytest

from ado_mcp.ado.client import build_http_client
from ado_mcp.config import Settings


@pytest.fixture
def settings():
    return Settings(org="test_org", project="test_project", pat="test_pat")


async def test_client_builds_ado_request(settings):
    seen = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json={})

    async with build_http_client(
        settings, transport=httpx2.MockTransport(handler)
    ) as client:
        await client.get("wit/workitems/1")

    request = seen[0]
    assert request.url.path == "/test_org/test_project/_apis/wit/workitems/1"
    assert request.url.params["api-version"] == "7.1"
    expected = base64.b64encode(b":test_pat").decode()
    assert request.headers["Authorization"] == f"Basic {expected}"


async def test_api_version_overriden_in_request(settings):
    seen = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json={})

    async with build_http_client(
        settings, transport=httpx2.MockTransport(handler)
    ) as client:
        await client.get("wit/workitems/1", params={"api-version": "6.0"})

    request = seen[0]
    assert request.url.params["api-version"] == "6.0"


async def test_302_from_handler_is_not_followed(settings):
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(302, headers={"Location": "https://example.com"})

    async with build_http_client(
        settings, transport=httpx2.MockTransport(handler)
    ) as client:
        response = await client.get("wit/workitems/1")

    assert response.status_code == 302
    assert response.headers["Location"] == "https://example.com"
