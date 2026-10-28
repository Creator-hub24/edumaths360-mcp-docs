"""A first MCP server: one tool and one resource, in under 30 lines.

Used by the "Build your first MCP server" tutorial.
Run it with:  python times_table_server.py
"""

import logging
import sys
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

mcp = MCPServer(name="times-table")


@mcp.tool(description="Return the multiplication table for a number.")
def times_table(
    number: Annotated[int, Field(ge=1, le=20, description="The table to print, 1 to 20.")],
    up_to: Annotated[int, Field(ge=1, le=20, description="Last multiplier.")] = 10,
) -> list[str]:
    return [f"{number} × {i} = {number * i}" for i in range(1, up_to + 1)]


@mcp.resource("tables://about", mime_type="text/plain")
def about() -> str:
    return "Times tables from 1 to 20. Call the times_table tool with a number."


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)  # never log to stdout
    mcp.run(transport="stdio")
