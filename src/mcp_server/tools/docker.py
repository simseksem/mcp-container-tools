"""Docker tools for container management and log reading."""

import asyncio
from typing import Any, Literal

from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

from mcp_server.utils.log_filter import filter_logs


class LogFilterInput(BaseModel):
    """Input schema for log filtering options."""

    min_level: Literal["trace", "debug", "info", "warn", "error", "fatal"] | None = Field(
        default=None, description="Minimum log level to show"
    )
    pattern: str | None = Field(default=None, description="Regex pattern to include")
    exclude_pattern: str | None = Field(default=None, description="Regex pattern to exclude")
    case_sensitive: bool = Field(default=False, description="Make pattern matching case sensitive")
    context_lines: int = Field(default=0, description="Number of context lines around matches")


class ContainerLogsInput(BaseModel):
    """Input schema for reading container logs."""

    container: str = Field(description="Container name or ID")
    tail: int = Field(default=100, description="Number of lines to show from the end")
    since: str | None = Field(default=None, description="Show logs since (e.g., '10m', '1h')")
    follow: bool = Field(default=False, description="Follow log output (returns last chunk)")
    # Filter options
    min_level: Literal["trace", "debug", "info", "warn", "error", "fatal"] | None = Field(
        default=None, description="Minimum log level to show"
    )
    pattern: str | None = Field(default=None, description="Regex pattern to include")
    exclude_pattern: str | None = Field(default=None, description="Regex pattern to exclude")
    context_lines: int = Field(default=0, description="Number of context lines around matches")


class ListContainersInput(BaseModel):
    """Input schema for listing containers."""

    all: bool = Field(default=False, description="Show all containers (default shows only running)")


class ContainerExecInput(BaseModel):
    """Input schema for executing command in container."""

    container: str = Field(description="Container name or ID")
    command: str = Field(description="Command to execute")


class DockerHost(BaseModel):
    """Docker host configuration."""

    host: str | None = Field(default=None, description="Docker host (e.g., 'ssh://user@remote', 'tcp://host:2375')")


def register_docker_tools(server: Server) -> None:
    """Register Docker tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="docker_logs",
                description="Read logs from a Docker container (local or remote)",
                inputSchema={
                    **ContainerLogsInput.model_json_schema(),
                    "properties": {
                        **ContainerLogsInput.model_json_schema().get("properties", {}),
                        **DockerHost.model_json_schema().get("properties", {}),
                    },
                },
            ),
            Tool(
                name="docker_ps",
                description="List Docker containers (local or remote)",
                inputSchema={
                    **ListContainersInput.model_json_schema(),
                    "properties": {
                        **ListContainersInput.model_json_schema().get("properties", {}),
                        **DockerHost.model_json_schema().get("properties", {}),
                    },
                },
            ),
            Tool(
                name="docker_inspect",
                description="Get detailed information about a container",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "container": {"type": "string", "description": "Container name or ID"},
                        "host": {"type": "string", "description": "Docker host (optional)"},
                    },
                    "required": ["container"],
                },
            ),
            Tool(
                name="docker_exec",
                description="Execute a command inside a running container",
                inputSchema={
                    **ContainerExecInput.model_json_schema(),
                    "properties": {
                        **ContainerExecInput.model_json_schema().get("properties", {}),
                        **DockerHost.model_json_schema().get("properties", {}),
                    },
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        host = arguments.get("host")

        match name:
            case "docker_logs":
                input_data = ContainerLogsInput.model_validate(arguments)
                output = await _get_container_logs(input_data, host)
                return [TextContent(type="text", text=output)]

            case "docker_ps":
                input_data = ListContainersInput.model_validate(arguments)
                output = await _list_containers(input_data, host)
                return [TextContent(type="text", text=output)]

            case "docker_inspect":
                container = arguments["container"]
                output = await _inspect_container(container, host)
                return [TextContent(type="text", text=output)]

            case "docker_exec":
                input_data = ContainerExecInput.model_validate(arguments)
                output = await _exec_in_container(input_data, host)
                return [TextContent(type="text", text=output)]

            case _:
                raise ValueError(f"Unknown tool: {name}")


def _build_docker_command(host: str | None, *args: str) -> list[str]:
    """Build docker command with optional remote host."""
    cmd = ["docker"]
    if host:
        cmd.extend(["--host", host])
    cmd.extend(args)
    return cmd


async def _run_docker_command(cmd: list[str]) -> str:
    """Execute a docker command and return output."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"Docker command failed: {error_msg}")

    return stdout.decode()


async def _get_container_logs(input_data: ContainerLogsInput, host: str | None) -> str:
    """Get logs from a Docker container."""
    cmd = _build_docker_command(host, "logs")

    cmd.extend(["--tail", str(input_data.tail)])

    if input_data.since:
        cmd.extend(["--since", input_data.since])

    cmd.append(input_data.container)

    output = await _run_docker_command(cmd)

    # Apply filtering if any filter options are set
    if input_data.min_level or input_data.pattern or input_data.exclude_pattern:
        output = filter_logs(
            output,
            min_level=input_data.min_level,
            pattern=input_data.pattern,
            exclude_pattern=input_data.exclude_pattern,
            context_lines=input_data.context_lines,
        )

    return output


async def _list_containers(input_data: ListContainersInput, host: str | None) -> str:
    """List Docker containers."""
    cmd = _build_docker_command(host, "ps")

    if input_data.all:
        cmd.append("--all")

    cmd.extend(["--format", "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"])

    return await _run_docker_command(cmd)


async def _inspect_container(container: str, host: str | None) -> str:
    """Get detailed container information."""
    cmd = _build_docker_command(host, "inspect", container)
    return await _run_docker_command(cmd)


async def _exec_in_container(input_data: ContainerExecInput, host: str | None) -> str:
    """Execute command in a container."""
    cmd = _build_docker_command(host, "exec", input_data.container)
    cmd.extend(["sh", "-c", input_data.command])
    return await _run_docker_command(cmd)
