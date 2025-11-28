#!/usr/bin/env python3
"""Test MCP server by sending JSON-RPC requests."""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server import create_server


async def test_tool(server, tool_name: str, arguments: dict) -> None:
    """Test a specific tool."""
    print(f"\n🔧 Testing: {tool_name}")
    print(f"   Args: {json.dumps(arguments)}")
    print("-" * 50)

    try:
        # Get the call_tool handler
        handlers = server._tool_handlers
        if handlers:
            for handler in handlers:
                result = await handler(tool_name, arguments)
                for content in result:
                    text = content.text if hasattr(content, 'text') else str(content)
                    # Truncate long output
                    if len(text) > 300:
                        text = text[:300] + "..."
                    print(text)
        print("✅ Success")
    except Exception as e:
        print(f"❌ Error: {e}")


async def test_list_tools(server) -> list:
    """List all available tools."""
    print("\n📋 Available Tools:")
    print("=" * 50)

    tools = []
    handlers = server._list_tools_handlers
    if handlers:
        for handler in handlers:
            result = await handler()
            tools.extend(result)

    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")

    return tools


async def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("  🧪 MCP Server Direct Test")
    print("=" * 60)

    # Create server
    server = create_server()
    print(f"\n✅ Server created: {server.name}")

    # List tools
    tools = await test_list_tools(server)

    # Test calculator
    await test_tool(server, "calculate", {
        "operation": "multiply",
        "a": 7,
        "b": 8
    })

    # Test Docker (if available)
    print("\n" + "-" * 60)
    response = input("Test docker_ps? [y/N]: ").strip().lower()
    if response == 'y':
        await test_tool(server, "docker_ps", {"all": False})

    # Test Kubernetes (if available)
    response = input("Test k8s_pods? [y/N]: ").strip().lower()
    if response == 'y':
        await test_tool(server, "k8s_pods", {"namespace": "default"})

    # Test Azure (if available)
    response = input("Test azure_exceptions? [y/N]: ").strip().lower()
    if response == 'y':
        await test_tool(server, "azure_exceptions", {
            "timespan": "PT1H",
            "limit": 5
        })

    print("\n" + "=" * 60)
    print("  ✅ MCP Server test completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
