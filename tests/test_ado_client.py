import base64
import json
from pathlib import Path

import httpx2
import pytest

from ado_mcp.ado.client import AdoClient, build_http_client
from ado_mcp.config import Settings

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


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


async def test_get_work_item_returns_work_item(settings):
    work_item = load_fixture("work_item_1.json")
    seen = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen.append(request)
        return httpx2.Response(200, json=work_item)

    async with build_http_client(
        settings, transport=httpx2.MockTransport(handler)
    ) as client:
        result = await AdoClient(client).get_work_item(1)

    assert result == work_item
    request = seen[0]
    assert request.url.path == "/test_org/test_project/_apis/wit/workitems/1"
    assert request.url.params["$expand"] == "relations"
    assert request.url.params["api-version"] == "7.1"


@pytest.mark.parametrize(
    "response",
    [
        httpx2.Response(404, json=load_fixture("non_existing_work_item.json")),
        httpx2.Response(
            302,
            headers={"Location": "https://spsprodweu5.vssps.visualstudio.com/_signin"},
        ),
    ],
    ids=["not_found", "signin_redirect"],
)
async def test_get_work_item_raises_on_error_response(settings, response):
    def handler(request: httpx2.Request) -> httpx2.Response:
        return response

    async with build_http_client(
        settings, transport=httpx2.MockTransport(handler)
    ) as client:
        with pytest.raises(httpx2.HTTPStatusError):
            await AdoClient(client).get_work_item(4444)
