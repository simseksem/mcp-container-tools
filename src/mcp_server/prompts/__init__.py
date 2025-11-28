"""Prompts module - Contains all MCP prompt handlers."""

from mcp.server import Server

from mcp_server.prompts.templates import register_prompt_templates


def register_prompts(server: Server) -> None:
    """Register all prompts with the MCP server."""
    register_prompt_templates(server)
