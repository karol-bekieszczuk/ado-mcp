import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ado_mcp.server import mcp


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


async def test_greet_rejects_times_above_max(client):
    with pytest.raises(ToolError, match="less than or equal to 5"):
        await client.call_tool("greet", {"name": "Karol", "times": 10})


async def test_greet_happy_path(client):
    result = await client.call_tool("greet", {"name": "Karol", "times": 3})
    assert result.data == "Hello, Karol! You have been greeted 3 times."


async def test_greet_tool_schema(client):
    tools = await client.list_tools()
    greet = next(t for t in tools if t.name == "greet")
    times = greet.input_schema["properties"]["times"]
    assert times["maximum"] == 5
    assert times["minimum"] == 1
    assert set(greet.input_schema["required"]) == {"name", "times"}
    assert greet.description
