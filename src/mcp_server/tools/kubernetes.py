"""Kubernetes tools for pod management and log reading."""

import asyncio
from typing import Any, Literal

from mcp.server import Server
from mcp.types import Tool, TextContent
from pydantic import BaseModel, Field

from mcp_server.utils.log_filter import filter_logs


class K8sContext(BaseModel):
    """Kubernetes context configuration."""

    context: str | None = Field(default=None, description="Kubernetes context to use")
    namespace: str = Field(default="default", description="Kubernetes namespace")


class PodLogsInput(BaseModel):
    """Input schema for reading pod logs."""

    pod: str = Field(description="Pod name (supports wildcards like 'my-app-*')")
    container: str | None = Field(default=None, description="Container name (for multi-container pods)")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    context: str | None = Field(default=None, description="Kubernetes context")
    tail: int = Field(default=100, description="Number of lines to show from the end")
    since: str | None = Field(default=None, description="Show logs since duration (e.g., '10m', '1h')")
    previous: bool = Field(default=False, description="Show logs from previous container instance")
    # Filter options
    min_level: Literal["trace", "debug", "info", "warn", "error", "fatal"] | None = Field(
        default=None, description="Minimum log level to show"
    )
    pattern: str | None = Field(default=None, description="Regex pattern to include")
    exclude_pattern: str | None = Field(default=None, description="Regex pattern to exclude")
    context_lines: int = Field(default=0, description="Number of context lines around matches")


class ListPodsInput(BaseModel):
    """Input schema for listing pods."""

    namespace: str = Field(default="default", description="Kubernetes namespace (use 'all' for all namespaces)")
    context: str | None = Field(default=None, description="Kubernetes context")
    selector: str | None = Field(default=None, description="Label selector (e.g., 'app=nginx')")


class PodActionInput(BaseModel):
    """Input schema for pod actions."""

    pod: str = Field(description="Pod name")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    context: str | None = Field(default=None, description="Kubernetes context")


class PodExecInput(BaseModel):
    """Input schema for executing commands in pods."""

    pod: str = Field(description="Pod name")
    command: str = Field(description="Command to execute")
    container: str | None = Field(default=None, description="Container name (for multi-container pods)")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    context: str | None = Field(default=None, description="Kubernetes context")


class DeploymentLogsInput(BaseModel):
    """Input schema for reading deployment logs."""

    deployment: str = Field(description="Deployment name")
    namespace: str = Field(default="default", description="Kubernetes namespace")
    context: str | None = Field(default=None, description="Kubernetes context")
    tail: int = Field(default=100, description="Number of lines per pod")
    since: str | None = Field(default=None, description="Show logs since duration")
    # Filter options
    min_level: Literal["trace", "debug", "info", "warn", "error", "fatal"] | None = Field(
        default=None, description="Minimum log level to show"
    )
    pattern: str | None = Field(default=None, description="Regex pattern to include")
    exclude_pattern: str | None = Field(default=None, description="Regex pattern to exclude")


def register_kubernetes_tools(server: Server) -> None:
    """Register Kubernetes tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="k8s_logs",
                description="Read logs from a Kubernetes pod",
                inputSchema=PodLogsInput.model_json_schema(),
            ),
            Tool(
                name="k8s_deployment_logs",
                description="Read logs from all pods in a deployment",
                inputSchema=DeploymentLogsInput.model_json_schema(),
            ),
            Tool(
                name="k8s_pods",
                description="List Kubernetes pods",
                inputSchema=ListPodsInput.model_json_schema(),
            ),
            Tool(
                name="k8s_describe",
                description="Get detailed information about a pod",
                inputSchema=PodActionInput.model_json_schema(),
            ),
            Tool(
                name="k8s_exec",
                description="Execute a command in a pod",
                inputSchema=PodExecInput.model_json_schema(),
            ),
            Tool(
                name="k8s_events",
                description="Get events for a namespace or pod",
                inputSchema=PodActionInput.model_json_schema(),
            ),
            Tool(
                name="k8s_contexts",
                description="List available Kubernetes contexts",
                inputSchema={"type": "object", "properties": {}},
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        match name:
            case "k8s_logs":
                input_data = PodLogsInput.model_validate(arguments)
                output = await _get_pod_logs(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_deployment_logs":
                input_data = DeploymentLogsInput.model_validate(arguments)
                output = await _get_deployment_logs(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_pods":
                input_data = ListPodsInput.model_validate(arguments)
                output = await _list_pods(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_describe":
                input_data = PodActionInput.model_validate(arguments)
                output = await _describe_pod(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_exec":
                input_data = PodExecInput.model_validate(arguments)
                output = await _exec_in_pod(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_events":
                input_data = PodActionInput.model_validate(arguments)
                output = await _get_events(input_data)
                return [TextContent(type="text", text=output)]

            case "k8s_contexts":
                output = await _list_contexts()
                return [TextContent(type="text", text=output)]

            case _:
                raise ValueError(f"Unknown tool: {name}")


def _build_kubectl_command(context: str | None, namespace: str | None, *args: str) -> list[str]:
    """Build kubectl command with context and namespace."""
    cmd = ["kubectl"]

    if context:
        cmd.extend(["--context", context])

    if namespace and namespace != "all":
        cmd.extend(["--namespace", namespace])
    elif namespace == "all":
        cmd.append("--all-namespaces")

    cmd.extend(args)
    return cmd


async def _run_kubectl_command(cmd: list[str]) -> str:
    """Execute a kubectl command and return output."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        error_msg = stderr.decode().strip()
        raise RuntimeError(f"kubectl command failed: {error_msg}")

    return stdout.decode()


async def _get_pod_logs(input_data: PodLogsInput) -> str:
    """Get logs from a Kubernetes pod."""
    cmd = _build_kubectl_command(input_data.context, input_data.namespace, "logs")

    cmd.extend(["--tail", str(input_data.tail)])

    if input_data.since:
        cmd.extend(["--since", input_data.since])

    if input_data.previous:
        cmd.append("--previous")

    if input_data.container:
        cmd.extend(["--container", input_data.container])

    cmd.append(input_data.pod)

    output = await _run_kubectl_command(cmd)

    # Apply filtering
    if input_data.min_level or input_data.pattern or input_data.exclude_pattern:
        output = filter_logs(
            output,
            min_level=input_data.min_level,
            pattern=input_data.pattern,
            exclude_pattern=input_data.exclude_pattern,
            context_lines=input_data.context_lines,
        )

    return output


async def _get_deployment_logs(input_data: DeploymentLogsInput) -> str:
    """Get logs from all pods in a deployment."""
    # First, get pods for the deployment
    selector_cmd = _build_kubectl_command(
        input_data.context,
        input_data.namespace,
        "get", "deployment", input_data.deployment,
        "-o", "jsonpath={.spec.selector.matchLabels}"
    )

    import json
    labels_output = await _run_kubectl_command(selector_cmd)

    # Parse labels and build selector
    try:
        labels = json.loads(labels_output.replace("'", '"'))
        selector = ",".join(f"{k}={v}" for k, v in labels.items())
    except json.JSONDecodeError:
        selector = f"app={input_data.deployment}"

    # Get logs from all pods with selector
    cmd = _build_kubectl_command(
        input_data.context,
        input_data.namespace,
        "logs",
        f"--selector={selector}",
        "--tail", str(input_data.tail),
        "--prefix",  # Add pod name prefix to each line
    )

    if input_data.since:
        cmd.extend(["--since", input_data.since])

    output = await _run_kubectl_command(cmd)

    # Apply filtering
    if input_data.min_level or input_data.pattern or input_data.exclude_pattern:
        output = filter_logs(
            output,
            min_level=input_data.min_level,
            pattern=input_data.pattern,
            exclude_pattern=input_data.exclude_pattern,
        )

    return output


async def _list_pods(input_data: ListPodsInput) -> str:
    """List Kubernetes pods."""
    cmd = _build_kubectl_command(input_data.context, input_data.namespace, "get", "pods")

    if input_data.selector:
        cmd.extend(["--selector", input_data.selector])

    cmd.extend(["-o", "wide"])

    return await _run_kubectl_command(cmd)


async def _describe_pod(input_data: PodActionInput) -> str:
    """Get detailed pod information."""
    cmd = _build_kubectl_command(
        input_data.context,
        input_data.namespace,
        "describe", "pod", input_data.pod
    )
    return await _run_kubectl_command(cmd)


async def _exec_in_pod(input_data: PodExecInput) -> str:
    """Execute command in a pod."""
    cmd = _build_kubectl_command(
        input_data.context,
        input_data.namespace,
        "exec", input_data.pod
    )

    if input_data.container:
        cmd.extend(["--container", input_data.container])

    cmd.extend(["--", "sh", "-c", input_data.command])

    return await _run_kubectl_command(cmd)


async def _get_events(input_data: PodActionInput) -> str:
    """Get events for a namespace or pod."""
    cmd = _build_kubectl_command(
        input_data.context,
        input_data.namespace,
        "get", "events",
        "--sort-by=.lastTimestamp"
    )

    if input_data.pod:
        cmd.extend(["--field-selector", f"involvedObject.name={input_data.pod}"])

    return await _run_kubectl_command(cmd)


async def _list_contexts() -> str:
    """List available Kubernetes contexts."""
    cmd = ["kubectl", "config", "get-contexts"]
    return await _run_kubectl_command(cmd)
