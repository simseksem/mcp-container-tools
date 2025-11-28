"""Data resources for exposing structured data."""

import json
from datetime import UTC, datetime

from mcp.server import Server
from mcp.types import Resource, TextContent


def register_data_resources(server: Server) -> None:
    """Register data resources with the server."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        return [
            Resource(
                uri="data://status",
                name="Server Status",
                description="Current server status and health information",
                mimeType="application/json",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri: str) -> list[TextContent]:
        if uri != "data://status":
            raise ValueError(f"Unknown resource: {uri}")

        status = _get_server_status()
        return [TextContent(type="text", text=json.dumps(status, indent=2))]


def _get_server_status() -> dict:
    """Get current server status information."""
    return {
        "status": "running",
        "timestamp": datetime.now(UTC).isoformat(),
        "health": {
            "memory": "ok",
            "connections": "ok",
        },
    }
