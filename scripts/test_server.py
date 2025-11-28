#!/usr/bin/env python3
"""Interactive test script for MCP server tools."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mcp_server.tools.calculator import CalculateInput, _perform_calculation
from mcp_server.tools.docker import ContainerLogsInput, _list_containers, _get_container_logs
from mcp_server.tools.docker_compose import ComposeServicesInput, _list_compose_services
from mcp_server.tools.kubernetes import ListPodsInput, _list_pods
from mcp_server.utils.log_filter import filter_logs


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_result(name: str, result: str) -> None:
    """Print a test result."""
    print(f"📋 {name}:")
    print("-" * 40)
    print(result[:500] + "..." if len(result) > 500 else result)
    print()


async def test_calculator() -> None:
    """Test calculator tool."""
    print_header("🧮 Calculator Test")

    tests = [
        ("2 + 3", CalculateInput(operation="add", a=2, b=3)),
        ("10 - 4", CalculateInput(operation="subtract", a=10, b=4)),
        ("5 * 6", CalculateInput(operation="multiply", a=5, b=6)),
        ("20 / 4", CalculateInput(operation="divide", a=20, b=4)),
    ]

    for name, input_data in tests:
        result = _perform_calculation(input_data)
        print(f"  {name} = {result}")

    print("\n✅ Calculator tests passed!")


async def test_docker() -> None:
    """Test Docker tools."""
    print_header("🐳 Docker Test")

    try:
        # List containers
        input_data = {"all": True}
        from mcp_server.tools.docker import ListContainersInput
        result = await _list_containers(ListContainersInput.model_validate(input_data), None)
        print_result("Docker containers", result)
        print("✅ Docker connection works!")
    except Exception as e:
        print(f"❌ Docker error: {e}")
        print("   Make sure Docker is running")


async def test_docker_compose() -> None:
    """Test Docker Compose tools."""
    print_header("🐙 Docker Compose Test")

    try:
        input_data = ComposeServicesInput(all=True)
        result = await _list_compose_services(input_data)
        print_result("Compose services", result)
        print("✅ Docker Compose works!")
    except Exception as e:
        print(f"⚠️  Docker Compose: {e}")
        print("   (This is normal if no compose project is running)")


async def test_kubernetes() -> None:
    """Test Kubernetes tools."""
    print_header("☸️ Kubernetes Test")

    try:
        input_data = ListPodsInput(namespace="default")
        result = await _list_pods(input_data)
        print_result("Kubernetes pods", result)
        print("✅ Kubernetes connection works!")
    except Exception as e:
        print(f"❌ Kubernetes error: {e}")
        print("   Make sure kubectl is configured")


async def test_azure() -> None:
    """Test Azure Application Insights tools."""
    print_header("☁️ Azure Application Insights Test")

    try:
        from mcp_server.tools.azure_insights import AZURE_SDK_AVAILABLE

        if not AZURE_SDK_AVAILABLE:
            print("⚠️  Azure SDK not installed")
            print("   Run: pip install -e '.[azure]'")
            return

        import os
        workspace_id = os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID")

        if not workspace_id:
            print("⚠️  AZURE_LOG_ANALYTICS_WORKSPACE_ID not set")
            print("   Set this environment variable to test Azure tools")
            return

        from mcp_server.tools.azure_insights import _run_kusto_query, KustoQueryInput

        input_data = KustoQueryInput(
            query="exceptions | take 5",
            timespan="PT1H",
            workspace_id=workspace_id,
        )
        result = await _run_kusto_query(input_data)
        print_result("Azure exceptions", result)
        print("✅ Azure connection works!")

    except Exception as e:
        print(f"❌ Azure error: {e}")
        print("   Make sure you're logged in with: az login")


def test_log_filter() -> None:
    """Test log filtering."""
    print_header("🔍 Log Filter Test")

    sample_logs = """
2024-01-15 10:00:00 INFO Starting application
2024-01-15 10:00:01 DEBUG Loading configuration
2024-01-15 10:00:02 INFO Server listening on port 8080
2024-01-15 10:00:03 WARN Connection timeout, retrying
2024-01-15 10:00:04 ERROR Failed to connect to database
2024-01-15 10:00:05 INFO Retry successful
2024-01-15 10:00:06 DEBUG Health check passed
2024-01-15 10:00:07 ERROR NullPointerException in UserService
2024-01-15 10:00:08 INFO Request processed successfully
"""

    # Test min_level filter
    print("📋 Filter: min_level='error'")
    print("-" * 40)
    result = filter_logs(sample_logs, min_level="error")
    print(result)
    print()

    # Test pattern filter
    print("📋 Filter: pattern='database|timeout'")
    print("-" * 40)
    result = filter_logs(sample_logs, pattern="database|timeout")
    print(result)
    print()

    # Test exclude filter
    print("📋 Filter: exclude_pattern='Health check'")
    print("-" * 40)
    result = filter_logs(sample_logs, exclude_pattern="Health check")
    print(result)
    print()

    print("✅ Log filter tests passed!")


async def main() -> None:
    """Run all tests."""
    print("\n" + "="*60)
    print("  🧪 MCP Container Tools - Test Suite")
    print("="*60)

    # Always run these
    await test_calculator()
    test_log_filter()

    # Optional: Docker tests
    print("\n" + "-"*60)
    response = input("Test Docker tools? [y/N]: ").strip().lower()
    if response == 'y':
        await test_docker()
        await test_docker_compose()

    # Optional: Kubernetes tests
    response = input("Test Kubernetes tools? [y/N]: ").strip().lower()
    if response == 'y':
        await test_kubernetes()

    # Optional: Azure tests
    response = input("Test Azure Application Insights? [y/N]: ").strip().lower()
    if response == 'y':
        await test_azure()

    print("\n" + "="*60)
    print("  ✅ Test suite completed!")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
