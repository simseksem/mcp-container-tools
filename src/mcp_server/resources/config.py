"""Configuration resources for exposing server settings."""

import json
import os

from mcp.server import Server
from mcp.types import Resource, TextContent


def register_config_resources(server: Server) -> None:
    """Register configuration resources with the server."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri="config://server",
                name="Server Configuration",
                description="Current server configuration settings",
                mimeType="application/json",
            ),
            Resource(
                uri="config://environment",
                name="Environment Variables",
                description="Available environment variables (filtered)",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> list[TextContent]:
        match uri:
            case "config://server":
                config = _get_server_config()
                return [TextContent(type="text", text=json.dumps(config, indent=2))]

            case "config://environment":
                env_vars = _get_filtered_environment()
                return [TextContent(type="text", text=json.dumps(env_vars, indent=2))]

            case _:
                raise ValueError(f"Unknown resource: {uri}")


def _get_server_config() -> dict:
    """Get current server configuration."""
    return {
        "name": "mcp-server",
        "version": "0.1.0",
        "capabilities": {
            "tools": True,
            "resources": True,
            "prompts": True,
        },
    }


def _get_filtered_environment() -> dict:
    """Get environment variables, filtering sensitive ones."""
    sensitive_patterns = ("KEY", "SECRET", "PASSWORD", "TOKEN", "CREDENTIAL")

    filtered_env = {}
    for key, value in os.environ.items():
        if any(pattern in key.upper() for pattern in sensitive_patterns):
            filtered_env[key] = "***REDACTED***"
        else:
            filtered_env[key] = value

    return filtered_env