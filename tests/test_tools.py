import re

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError

from ado_mcp.server import create_server


@pytest.fixture
async def client():
    async with Client(create_server()) as c:
        yield c


async def test_greet_rejects_times_above_max(client):
    with pytest.raises(ToolError, match="less than or equal to 5"):
        await client.call_tool("greet", {"name": "Karol", "times": 10})


async def test_greet_rejects_non_numeric_times(client):
    exptected = "Input should be a valid integer"
    with pytest.raises(ToolError, match=re.escape(exptected)):
        await client.call_tool("greet", {"name": "Karol", "times": "abc"})


async def test_greet_happy_path(client):
    result = await client.call_tool("greet", {"name": "Karol", "times": 3})
    assert result.data == "Hello, Karol! You have been greeted 3 times."


async def test_greet_empty_name(client):
    expected = "String should have at least 1 character [type=string_too_short, input_value='', input_type=str"
    with pytest.raises(ToolError, match=re.escape(expected)):
        await client.call_tool("greet", {"name": "", "times": 3})


async def test_greet_whitespace_name(client):
    expected = "String should have at least 1 character"
    with pytest.raises(ToolError, match=re.escape(expected)):
        await client.call_tool("greet", {"name": "    ", "times": 3})


async def test_greet_tool_schema(client):
    tools = await client.list_tools()
    greet = next(t for t in tools if t.name == "greet")
    times = greet.input_schema["properties"]["times"]
    assert times["maximum"] == 5
    assert times["minimum"] == 1
    assert set(greet.input_schema["required"]) == {"name", "times"}
    assert greet.description
    name = greet.input_schema["properties"]["name"]
    assert name["type"] == "string"
    assert name["minLength"] == 1
