import httpx2
import pytest
from fastmcp import Client, Context

from ado_mcp.server import create_server


async def test_server_fails_to_start_with_invalid_config(monkeypatch):
    monkeypatch.setenv("ADO_ORG", "")
    with pytest.raises(RuntimeError, match="Client failed to connect"):
        async with Client(create_server()):
            pass


async def test_lifespan_provides_http_client_and_closes_it():
    seen = []
    clients = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        print(request)
        seen.append(request)
        return httpx2.Response(200, json={"ok": True})

    async def probe(ctx: Context) -> dict:
        http_client = ctx.lifespan_context["http_client"]
        print(http_client)
        clients.append(http_client)
        response = await http_client.get("wit/workitems/1")
        return response.json()

    mcp = create_server(transport=httpx2.MockTransport(handler))
    mcp.tool(probe)

    async with Client(mcp) as client:
        result = await client.call_tool("probe", {})
        print(result)
        assert result.data == {"ok": True}
        assert not clients[0].is_closed

    assert seen[0].url.path == "/myorg/myproject/_apis/wit/workitems/1"
    assert clients[0].is_closed
