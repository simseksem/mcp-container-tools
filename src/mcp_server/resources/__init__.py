"""Resources module - Contains all MCP resource handlers."""

from mcp.server import Server

from mcp_server.resources.config import register_config_resources
from mcp_server.resources.data import register_data_resources


def register_resources(server: Server) -> None:
    """Register all resources with the MCP server."""
    register_config_resources(server)
    register_data_resources(server)
