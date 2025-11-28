"""Tools module - Contains all MCP tool handlers."""

from mcp.server import Server

from mcp_server.tools.azure_insights import register_azure_insights_tools
from mcp_server.tools.docker import register_docker_tools
from mcp_server.tools.docker_compose import register_compose_tools
from mcp_server.tools.file_operations import register_file_tools
from mcp_server.tools.kubernetes import register_kubernetes_tools


def register_tools(server: Server) -> None:
    """Register all tools with the MCP server."""
    register_file_tools(server)
    register_docker_tools(server)
    register_compose_tools(server)
    register_kubernetes_tools(server)
    register_azure_insights_tools(server)
