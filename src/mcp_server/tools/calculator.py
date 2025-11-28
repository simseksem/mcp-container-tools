"""Calculator tools for basic mathematical operations."""

from typing import Any

from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field


class CalculateInput(BaseModel):
    """Input schema for calculator operations."""

    operation: str = Field(
        description="The operation to perform: add, subtract, multiply, divide"
    )
    a: float = Field(description="First operand")
    b: float = Field(description="Second operand")


def register_calculator_tools(server: Server) -> None:
    """Register calculator tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="calculate",
                description="Perform basic math operations (add, subtract, multiply, divide)",
                inputSchema=CalculateInput.model_json_schema(),
            )
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if name != "calculate":
            raise ValueError(f"Unknown tool: {name}")

        input_data = CalculateInput.model_validate(arguments)
        result = _perform_calculation(input_data)

        return [TextContent(type="text", text=str(result))]


def _perform_calculation(input_data: CalculateInput) -> float:
    """Execute the mathematical operation."""
    operations = {
        "add": lambda a, b: a + b,
        "subtract": lambda a, b: a - b,
        "multiply": lambda a, b: a * b,
        "divide": lambda a, b: a / b if b != 0 else float("inf"),
    }

    operation_func = operations.get(input_data.operation)
    if operation_func is None:
        raise ValueError(f"Unknown operation: {input_data.operation}")

    return operation_func(input_data.a, input_data.b)
