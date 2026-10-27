import os
from importlib.metadata import version
from typing import Annotated, Literal

from fastmcp import Context, FastMCP
from fastmcp.prompts import Message
from pydantic import Field, StringConstraints

HTTP_SECURITY = {"host_origin_protection": True}


def greet(
    name: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1),
        Field(description="The name of the person to greet"),
    ],
    times: Annotated[
        int, Field(ge=1, le=5, description="The number of times to greet")
    ],
) -> str:
    """Greets a person by name specified number of times. Use when asked to greet someone. Returns a greeting message with info how many times the person was greeted."""
    return f"Hello, {name}! You have been greeted {times} times."


async def server_metadata(ctx: Context) -> dict:
    """Returns server metadata and available MCP primitives as JSON."""
    server = ctx.fastmcp
    return {
        "name": server.name,
        "version": version("ado-mcp"),
        "fastmcp_version": version("fastmcp"),
        "primitives": {
            "tools": [t.name for t in await server.list_tools()],
            "resources": [r.name for r in await server.list_resources()],
            "resource_templates": [
                r.name for r in await server.list_resource_templates()
            ],
            "prompts": [p.name for p in await server.list_prompts()],
        },
    }


def greeting(name: str) -> str:
    """Greeting resource. Returns a greeting message for the given name."""
    return f"# Hello {name}\n..."


def greeting_prompt(
    names: Annotated[
        str,
        Field(
            min_length=1, description="names to pass to the prompt separated by commas"
        ),
    ],
    style: Annotated[
        Literal["formal", "friendly"], Field(description="output style")
    ] = "formal",
    times: Annotated[
        int, Field(ge=1, le=5, description="The number of times to greet")
    ] = 1,
) -> list[Message]:
    """Greeting prompt. Returns a list of messages with instructions to greet the given names in the specified style.
    Allowed styles: formal, friendly. Use when asked to greet someone."""
    return [
        Message(
            f"using the tool greet please greet the users {names} in {style} style {times} times",
            role="user",
        )
    ]


def create_server() -> FastMCP:
    mcp = FastMCP("ado-mcp")
    mcp.tool(greet)
    mcp.resource("server://info", mime_type="application/json")(server_metadata)
    mcp.resource("greeting://{name}")(greeting)
    mcp.prompt(greeting_prompt)
    return mcp


def main() -> None:
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in ("stdio", "http"):
        raise SystemExit(
            f"Unknown MCP_TRANSPORT={transport!r}, expected 'stdio' or 'http'"
        )

    mcp = create_server()

    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport="http", host="127.0.0.1", port=8000, **HTTP_SECURITY)


if __name__ == "__main__":
    main()
