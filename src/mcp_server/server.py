"""Main MCP server module."""

import asyncio
import logging

from mcp.server import Server
from mcp.server.stdio import stdio_server

from mcp_server.prompts import register_prompts
from mcp_server.resources import register_resources
from mcp_server.tools import register_tools

logger = logging.getLogger(__name__)


def create_server() -> Server:
    """Create and configure the MCP server with all handlers."""
    server = Server("mcp-server")

    register_tools(server)
    register_resources(server)
    register_prompts(server)

    return server


async def run_server() -> None:
    """Run the MCP server using stdio transport."""
    server = create_server()

    async with stdio_server() as (read_stream, write_stream):
        logger.info("MCP server started")
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    """Entry point for the MCP server."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
