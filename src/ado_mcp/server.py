from importlib.metadata import version
from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

mcp = FastMCP("ado-mcp")


@mcp.tool
def greet(
    name: Annotated[str, "The name of the person to greet"],
    times: Annotated[
        int, Field(ge=1, le=5, description="The number of times to greet")
    ],
) -> str:
    """Greets a person by name specified number of times. Use when asked to greet someone. Returns a greeting message with info how many times the person was greeted."""
    return f"Hello, {name}! You have been greeted {times} times."


@mcp.resource("server://info", mime_type="application/json")
async def server_metadata() -> dict:
    """Returns server metadata and available MCP primitives as JSON."""
    return {
        "name": mcp.name,
        "version": version("ado-mcp"),
        "fastmcp_version": version("fastmcp"),
        "primitives": {
            "tools": [t.name for t in await mcp.list_tools()],
            "resources": [r.name for r in await mcp.list_resources()],
            "resource_templates": [r.name for r in await mcp.list_resource_templates()],
            "prompts": [p.name for p in await mcp.list_prompts()],
        },
    }


@mcp.resource("greeting://{name}")
def greeting(name: str) -> str:
    """Greeting resource. Returns a greeting message for the given name."""
    return f"# Hello {name}\n..."


def main() -> None:
    mcp.run()  # default transport = stdio


if __name__ == "__main__":
    main()
