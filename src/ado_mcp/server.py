from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

mcp = FastMCP("ado-mcp")

@mcp.tool
def greet(name: Annotated[str, "The name of the person to greet"], times: Annotated[int, Field(ge=1, le=5, description="The number of times to greet")]) -> str:
    """Greets a person by name specified number of times. Use when asked to greet someone. Returns a greeting message with info how many times the person was greeted."""
    return f"Hello, {name}! You have been greeted {times} times."

def main() -> None:
    mcp.run()  # default transport = stdio

if __name__ == "__main__": 
    main()