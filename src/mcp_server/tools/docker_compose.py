"""Docker Compose tools for service management and logs."""

import asyncio
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field


class ComposeLogsInput(BaseModel):
    """Input schema for reading compose service logs."""

    service: str | None = Field(default=None, description="Service name (omit for all services)")
    tail: int = Field(default=100, description="Number of lines to show from the end")
    since: str | None = Field(default=None, description="Show logs since timestamp (e.g., '10m', '1h')")
    project_dir: str | None = Field(default=None, description="Path to docker-compose.yml directory")
    follow: bool = Field(default=False, description="Follow log output")


class ComposeServicesInput(BaseModel):
    """Input schema for listing compose services."""

    project_dir: str | None = Field(default=None, description="Path to docker-compose.yml directory")
    all: bool = Field(default=False, description="Show all services (including stopped)")


class ComposeServiceActionInput(BaseModel):
    """Input schema for service actions."""

    service: str | None = Field(default=None, description="Service name (omit for all services)")
    project_dir: str | None = Field(default=None, description="Path to docker-compose.yml directory")


def register_compose_tools(server: Server) -> None:
    """Register Docker Compose tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="compose_logs",
                description="Read logs from Docker Compose services",
                inputSchema=ComposeLogsInput.model_json_schema(),
            ),
            Tool(
                name="compose_ps",
                description="List Docker Compose services and their status",
                inputSchema=ComposeServicesInput.model_json_schema(),
            ),
            Tool(
                name="compose_up",
                description="Start Docker Compose services",
                inputSchema=ComposeServiceActionInput.model_json_schema(),
            ),
            Tool(
                name="compose_down",
                description="Stop Docker Compose services",
                inputSchema=ComposeServiceActionInput.model_json_schema(),
            ),
            Tool(
                name="compose_restart",
                description="Restart Docker Compose services",
                inputSchema=ComposeServiceActionInput.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        match name:
            case "compose_logs":
                input_data = ComposeLogsInput.model_validate(arguments)
                output = await _get_compose_logs(input_data)
                return [TextContent(type="text", text=output)]

            case "compose_ps":
                input_data = ComposeServicesInput.model_validate(arguments)
                output = await _list_compose_services(input_data)
                return [TextContent(type="text", text=output)]

            case "compose_up":
                input_data = ComposeServiceActionInput.model_validate(arguments)
                output = await _compose_action("up", input_data)
                return [TextContent(type="text", text=output)]

            case "compose_down":
                input_data = ComposeServiceActionInput.model_validate(arguments)
                output = await _compose_action("down", input_data)
                return [TextContent(type="text", text=output)]

            case "compose_restart":
                input_data = ComposeServiceActionInput.model_validate(arguments)
                output = await _compose_action("restart", input_data)
                return [TextContent(type="text", text=output)]

            case _:
                raise ValueError(f"Unknown tool: {name}")


async def _run_compose_command(cmd: list[str], cwd: str | None = None) -> str:
    """Execute a docker compose command and return output."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"Docker Compose command failed: {error_msg}")

    return stdout.decode()


async def _get_compose_logs(input_data: ComposeLogsInput) -> str:
    """Get logs from Docker Compose services."""
    cmd = ["docker", "compose", "logs"]

    cmd.extend(["--tail", str(input_data.tail)])

    if input_data.since:
        cmd.extend(["--since", input_data.since])

    if not input_data.follow:
        cmd.append("--no-log-prefix")

    if input_data.service:
        cmd.append(input_data.service)

    return await _run_compose_command(cmd, input_data.project_dir)


async def _list_compose_services(input_data: ComposeServicesInput) -> str:
    """List Docker Compose services."""
    cmd = ["docker", "compose", "ps"]

    if input_data.all:
        cmd.append("--all")

    cmd.append("--format")
    cmd.append("table {{.Name}}\t{{.Service}}\t{{.Status}}\t{{.Ports}}")

    return await _run_compose_command(cmd, input_data.project_dir)


async def _compose_action(action: str, input_data: ComposeServiceActionInput) -> str:
    """Execute a compose action (up/down/restart)."""
    cmd = ["docker", "compose", action]

    if action == "up":
        cmd.append("-d")

    if input_data.service:
        cmd.append(input_data.service)

    return await _run_compose_command(cmd, input_data.project_dir)
