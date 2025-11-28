#!/usr/bin/env python3
"""Test MCP server tools directly."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


async def test_docker():
    """Test Docker tools."""
    print("\n🐳 Docker Test")
    print("=" * 50)

    from mcp_server.tools.docker import ListContainersInput, _list_containers

    try:
        result = await _list_containers(ListContainersInput(all=True), None)
        print(result[:500] if len(result) > 500 else result)
        print("✅ Docker works!")
    except Exception as e:
        print(f"❌ {e}")


async def test_kubernetes():
    """Test Kubernetes tools."""
    print("\n☸️ Kubernetes Test")
    print("=" * 50)

    from mcp_server.tools.kubernetes import ListPodsInput, _list_pods

    try:
        result = await _list_pods(ListPodsInput(namespace="default"))
        print(result[:500] if len(result) > 500 else result)
        print("✅ Kubernetes works!")
    except Exception as e:
        print(f"❌ {e}")


async def test_azure():
    """Test Azure tools."""
    print("\n☁️ Azure Application Insights Test")
    print("=" * 50)

    try:
        from mcp_server.tools.azure_insights import AZURE_SDK_AVAILABLE

        if not AZURE_SDK_AVAILABLE:
            print("⚠️  Azure SDK not installed")
            print("   Run: pip install -e '.[azure]'")
            return

        import os
        if not os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID"):
            print("⚠️  AZURE_LOG_ANALYTICS_WORKSPACE_ID not set")
            return

        from mcp_server.tools.azure_insights import (
            ExceptionsQueryInput, _query_exceptions
        )

        result = await _query_exceptions(
            ExceptionsQueryInput(timespan="PT1H", limit=5)
        )
        print(result[:500] if len(result) > 500 else result)
        print("✅ Azure works!")
    except Exception as e:
        print(f"❌ {e}")


async def test_log_filter():
    """Test log filtering."""
    print("\n🔍 Log Filter Test")
    print("=" * 50)

    from mcp_server.utils.log_filter import filter_logs

    logs = """2024-01-15 10:00:00 INFO Application started
2024-01-15 10:00:01 DEBUG Loading config
2024-01-15 10:00:02 ERROR Database connection failed
2024-01-15 10:00:03 WARN Retrying connection
2024-01-15 10:00:04 ERROR Timeout exceeded
2024-01-15 10:00:05 INFO Connection restored"""

    print("Original logs:")
    print(logs)
    print("\nFiltered (min_level='error'):")
    print(filter_logs(logs, min_level="error"))
    print("✅ Log filter works!")


async def main():
    print("\n" + "=" * 60)
    print("  🧪 MCP Container Tools - Quick Test")
    print("=" * 60)

    await test_log_filter()

    # Optional tests
    print("\n" + "-" * 60)
    if input("Test Docker? [y/N]: ").lower() == 'y':
        await test_docker()

    if input("Test Kubernetes? [y/N]: ").lower() == 'y':
        await test_kubernetes()

    if input("Test Azure? [y/N]: ").lower() == 'y':
        await test_azure()

    print("\n" + "=" * 60)
    print("  ✅ Tests completed!")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
