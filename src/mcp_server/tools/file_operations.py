"""File operation tools for reading and listing files."""

from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field


class ReadFileInput(BaseModel):
    """Input schema for reading a file."""

    path: str = Field(description="Path to the file to read")


class ListDirectoryInput(BaseModel):
    """Input schema for listing directory contents."""

    path: str = Field(description="Path to the directory to list")


def register_file_tools(server: Server) -> None:
    """Register file operation tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="read_file",
                description="Read the contents of a file",
                inputSchema=ReadFileInput.model_json_schema(),
            ),
            Tool(
                name="list_directory",
                description="List contents of a directory",
                inputSchema=ListDirectoryInput.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        match name:
            case "read_file":
                input_data = ReadFileInput.model_validate(arguments)
                content = _read_file(input_data.path)
                return [TextContent(type="text", text=content)]

            case "list_directory":
                input_data = ListDirectoryInput.model_validate(arguments)
                content = _list_directory(input_data.path)
                return [TextContent(type="text", text=content)]

            case _:
                raise ValueError(f"Unknown tool: {name}")


def _read_file(path: str) -> str:
    """Read and return file contents."""
    file_path = Path(path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    return file_path.read_text(encoding="utf-8")


def _list_directory(path: str) -> str:
    """List directory contents and return as formatted string."""
    dir_path = Path(path)

    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not dir_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    entries = []
    for entry in sorted(dir_path.iterdir()):
        entry_type = "dir" if entry.is_dir() else "file"
        size = entry.stat().st_size if entry.is_file() else "-"
        entries.append(f"{entry_type}\t{size}\t{entry.name}")

    return "\n".join(entries) if entries else "(empty directory)"
