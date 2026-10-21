import re

import pytest
from fastmcp import Client
from fastmcp.exceptions import MCPError

from ado_mcp.server import mcp


@pytest.fixture
async def client():
    async with Client(mcp) as c:
        yield c


async def test_list_prompts(client):
    prompts = await client.list_prompts()
    assert len(prompts) > 0
    assert {prompt.name for prompt in prompts} == {"greeting_prompt"}
    args = {a.name: a for a in prompts[0].arguments}
    assert args["names"].required is True
    assert "formal" in args["style"].description


async def test_greet_prompt_happy_path(client):
    result = await client.get_prompt_mcp(
        "greeting_prompt", {"names": "Karol", "style": "formal", "times": 3}
    )
    assert (
        result.messages[0].content.text
        == "using the tool greet please greet the users Karol in formal style 3 times"
    )


async def test_greet_prompt_missing_style_and_times_happy_path(client):
    result = await client.get_prompt_mcp("greeting_prompt", {"names": "Karol"})
    assert (
        result.messages[0].content.text
        == "using the tool greet please greet the users Karol in formal style 1 times"
    )


async def test_greet_prompt_invalid_style(client):
    expected = "Could not convert argument 'style' with value 'invalid' to expected type typing"
    with pytest.raises(MCPError, match=re.escape(expected)):
        await client.get_prompt_mcp(
            "greeting_prompt", {"names": "Karol", "style": "invalid"}
        )


async def test_greet_prompt_invalid_name_and_style(client):
    expected = (
        "Could not convert argument 'names' with value '' to expected type typing"
    )
    with pytest.raises(MCPError, match=re.escape(expected)):
        await client.get_prompt_mcp("greeting_prompt", {"names": "", "style": "abc"})


async def test_greet_prompt_missing_names_parameter(client):
    with pytest.raises(
        MCPError,
        match=re.escape(
            "Error rendering prompt 'greeting_prompt': Missing required arguments: {'names'}"
        ),
    ):
        await client.get_prompt_mcp("greeting_prompt", {"style": "formal"})


async def test_greet_prompt_missing_parameters(client):
    with pytest.raises(
        MCPError,
        match=re.escape(
            "Error rendering prompt 'greeting_prompt': Missing required arguments: {'names'}"
        ),
    ):
        await client.get_prompt_mcp("greeting_prompt", {})
