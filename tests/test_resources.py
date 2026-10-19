import json
from importlib.metadata import version

import pytest
from fastmcp import Client
from fastmcp.exceptions import MCPError

from ado_mcp.server import mcp


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


async def test_static_resource_missing(client):
    with pytest.raises(MCPError, match="Resource not found: 'docs://nope'"):
        await client.read_resource("docs://nope")


async def test_static_resource_happy_path(client):
    result = await client.read_resource("server://info")
    data = json.loads(result[0].text)
    assert data["name"] == "ado-mcp"
    assert data["version"] == version("ado-mcp")
    assert data["fastmcp_version"] == version("fastmcp")
    assert result[0].mime_type == "application/json"


async def test_dynamic_resource_missing(client):
    with pytest.raises(MCPError, match="Resource not found: 'greeting://'"):
        await client.read_resource("greeting://")


async def test_dynamic_resource_with_forward_slash(client):
    with pytest.raises(MCPError, match="Resource not found: 'greeting://a/b'"):
        await client.read_resource("greeting://a/b")


async def test_dynamic_resource_happy_path(client):
    output = await client.read_resource("greeting://Karol%20Kowalski")
    assert output[0].uri == "greeting://Karol%20Kowalski"
    assert output[0].text == "# Hello Karol Kowalski\n..."


async def test_resource_list(client):
    resources = await client.list_resources()
    assert "server://info" in [t.uri for t in resources]


async def test_resource_templates_list_has_greeting(client):
    templates = await client.list_resource_templates()
    assert "greeting://{name}" in [t.uri_template for t in templates]
