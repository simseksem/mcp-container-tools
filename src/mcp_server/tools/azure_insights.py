"""Azure Application Insights tools for querying logs and metrics."""

import json
import os
from datetime import timedelta
from typing import Any, Literal

from mcp.server import Server
from mcp.types import TextContent, Tool
from pydantic import BaseModel, Field

try:
    from azure.identity import DefaultAzureCredential
    from azure.monitor.query import LogsQueryClient, MetricsQueryClient

    AZURE_SDK_AVAILABLE = True
except ImportError:
    AZURE_SDK_AVAILABLE = False


class KustoQueryInput(BaseModel):
    """Input schema for running Kusto queries."""

    query: str = Field(description="Kusto query to execute")
    timespan: str = Field(
        default="PT1H",
        description="ISO 8601 duration (PT1H=1 hour, P1D=1 day, P7D=7 days)",
    )
    workspace_id: str | None = Field(
        default=None,
        description="Log Analytics workspace ID (or set AZURE_LOG_ANALYTICS_WORKSPACE_ID)",
    )


class ExceptionsQueryInput(BaseModel):
    """Input schema for querying exceptions."""

    timespan: str = Field(default="PT1H", description="ISO 8601 duration")
    limit: int = Field(default=50, description="Maximum number of results")
    severity: Literal["all", "error", "critical"] | None = Field(
        default=None, description="Filter by severity level"
    )
    search: str | None = Field(default=None, description="Search in exception messages")


class TracesQueryInput(BaseModel):
    """Input schema for querying traces."""

    timespan: str = Field(default="PT1H", description="ISO 8601 duration")
    limit: int = Field(default=100, description="Maximum number of results")
    severity: Literal["verbose", "info", "warning", "error", "critical"] | None = Field(
        default=None, description="Filter by severity level"
    )
    search: str | None = Field(default=None, description="Search in trace messages")


class RequestsQueryInput(BaseModel):
    """Input schema for querying requests."""

    timespan: str = Field(default="PT1H", description="ISO 8601 duration")
    limit: int = Field(default=100, description="Maximum number of results")
    failed_only: bool = Field(default=False, description="Show only failed requests")
    min_duration_ms: int | None = Field(
        default=None, description="Minimum duration in milliseconds"
    )
    url_filter: str | None = Field(default=None, description="Filter by URL pattern")


class DependenciesQueryInput(BaseModel):
    """Input schema for querying dependencies."""

    timespan: str = Field(default="PT1H", description="ISO 8601 duration")
    limit: int = Field(default=100, description="Maximum number of results")
    failed_only: bool = Field(default=False, description="Show only failed dependencies")
    type_filter: str | None = Field(
        default=None, description="Filter by type (HTTP, SQL, Azure, etc.)"
    )


class MetricsQueryInput(BaseModel):
    """Input schema for querying metrics."""

    metric_name: str = Field(
        description="Metric name (e.g., requests/count, exceptions/count)"
    )
    timespan: str = Field(default="PT1H", description="ISO 8601 duration")
    interval: str = Field(default="PT5M", description="Aggregation interval")
    aggregation: Literal["avg", "min", "max", "sum", "count"] = Field(
        default="avg", description="Aggregation type"
    )
    resource_id: str | None = Field(
        default=None,
        description="Azure resource ID (uses AZURE_APP_INSIGHTS_RESOURCE_ID env if not set)",
    )


class AvailabilityQueryInput(BaseModel):
    """Input schema for querying availability tests."""

    timespan: str = Field(default="P1D", description="ISO 8601 duration")
    limit: int = Field(default=50, description="Maximum number of results")
    test_name: str | None = Field(default=None, description="Filter by test name")
    failed_only: bool = Field(default=False, description="Show only failed tests")


def _parse_timespan(timespan: str) -> timedelta:
    """Parse ISO 8601 duration to timedelta."""
    # Simple parser for common formats
    if timespan.startswith("PT"):
        value = timespan[2:-1]
        unit = timespan[-1]
        if unit == "H":
            return timedelta(hours=int(value))
        elif unit == "M":
            return timedelta(minutes=int(value))
        elif unit == "S":
            return timedelta(seconds=int(value))
    elif timespan.startswith("P"):
        value = timespan[1:-1]
        unit = timespan[-1]
        if unit == "D":
            return timedelta(days=int(value))
        elif unit == "W":
            return timedelta(weeks=int(value))
    return timedelta(hours=1)


def _get_workspace_id(provided: str | None) -> str:
    """Get workspace ID from parameter or environment."""
    workspace_id = provided or os.getenv("AZURE_LOG_ANALYTICS_WORKSPACE_ID")
    if not workspace_id:
        raise ValueError(
            "Workspace ID required. Set AZURE_LOG_ANALYTICS_WORKSPACE_ID or provide workspace_id"
        )
    return workspace_id


def _get_resource_id(provided: str | None) -> str:
    """Get resource ID from parameter or environment."""
    resource_id = provided or os.getenv("AZURE_APP_INSIGHTS_RESOURCE_ID")
    if not resource_id:
        raise ValueError(
            "Resource ID required. Set AZURE_APP_INSIGHTS_RESOURCE_ID or provide resource_id"
        )
    return resource_id


def _format_table_results(tables: list) -> str:
    """Format query results as readable text."""
    if not tables:
        return "No results found."

    results = []
    for table in tables:
        columns = [col.name for col in table.columns]
        for row in table.rows:
            record = dict(zip(columns, row, strict=False))
            results.append(record)

    return json.dumps(results, indent=2, default=str)


def register_azure_insights_tools(server: Server) -> None:
    """Register Azure Application Insights tools with the server."""

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="azure_query",
                description="Run a custom Kusto query on Application Insights logs",
                inputSchema=KustoQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_exceptions",
                description="Query application exceptions and errors",
                inputSchema=ExceptionsQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_traces",
                description="Query application traces and logs",
                inputSchema=TracesQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_requests",
                description="Query HTTP requests to your application",
                inputSchema=RequestsQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_dependencies",
                description="Query external dependencies (HTTP, SQL, etc.)",
                inputSchema=DependenciesQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_metrics",
                description="Query Application Insights metrics",
                inputSchema=MetricsQueryInput.model_json_schema(),
            ),
            Tool(
                name="azure_availability",
                description="Query availability test results",
                inputSchema=AvailabilityQueryInput.model_json_schema(),
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        if not AZURE_SDK_AVAILABLE:
            return [
                TextContent(
                    type="text",
                    text="Azure SDK not installed. Run: pip install azure-identity azure-monitor-query",  # noqa: E501
                )
            ]

        match name:
            case "azure_query":
                input_data = KustoQueryInput.model_validate(arguments)
                output = await _run_kusto_query(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_exceptions":
                input_data = ExceptionsQueryInput.model_validate(arguments)
                output = await _query_exceptions(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_traces":
                input_data = TracesQueryInput.model_validate(arguments)
                output = await _query_traces(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_requests":
                input_data = RequestsQueryInput.model_validate(arguments)
                output = await _query_requests(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_dependencies":
                input_data = DependenciesQueryInput.model_validate(arguments)
                output = await _query_dependencies(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_metrics":
                input_data = MetricsQueryInput.model_validate(arguments)
                output = await _query_metrics(input_data)
                return [TextContent(type="text", text=output)]

            case "azure_availability":
                input_data = AvailabilityQueryInput.model_validate(arguments)
                output = await _query_availability(input_data)
                return [TextContent(type="text", text=output)]

            case _:
                raise ValueError(f"Unknown tool: {name}")


async def _run_kusto_query(input_data: KustoQueryInput) -> str:
    """Run a custom Kusto query."""
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)

    workspace_id = _get_workspace_id(input_data.workspace_id)
    timespan = _parse_timespan(input_data.timespan)

    response = client.query_workspace(
        workspace_id=workspace_id,
        query=input_data.query,
        timespan=timespan,
    )

    return _format_table_results(response.tables)


async def _query_exceptions(input_data: ExceptionsQueryInput) -> str:
    """Query application exceptions."""
    where_clauses = []

    if input_data.severity == "error":
        where_clauses.append("severityLevel >= 3")
    elif input_data.severity == "critical":
        where_clauses.append("severityLevel >= 4")

    if input_data.search:
        where_clauses.append(f'outerMessage contains "{input_data.search}"')

    where_str = " and ".join(where_clauses) if where_clauses else "1==1"

    query = f"""
    exceptions
    | where {where_str}
    | order by timestamp desc
    | take {input_data.limit}
    | project timestamp, problemId, outerType, outerMessage, severityLevel,
              details=tostring(details), cloud_RoleName, operation_Id
    """

    return await _run_kusto_query(
        KustoQueryInput(query=query, timespan=input_data.timespan)
    )


async def _query_traces(input_data: TracesQueryInput) -> str:
    """Query application traces."""
    severity_map = {"verbose": 0, "info": 1, "warning": 2, "error": 3, "critical": 4}
    where_clauses = []

    if input_data.severity:
        level = severity_map.get(input_data.severity, 1)
        where_clauses.append(f"severityLevel == {level}")

    if input_data.search:
        where_clauses.append(f'message contains "{input_data.search}"')

    where_str = " and ".join(where_clauses) if where_clauses else "1==1"

    query = f"""
    traces
    | where {where_str}
    | order by timestamp desc
    | take {input_data.limit}
    | project timestamp, message, severityLevel, cloud_RoleName, operation_Id
    """

    return await _run_kusto_query(
        KustoQueryInput(query=query, timespan=input_data.timespan)
    )


async def _query_requests(input_data: RequestsQueryInput) -> str:
    """Query HTTP requests."""
    where_clauses = []

    if input_data.failed_only:
        where_clauses.append("success == false")

    if input_data.min_duration_ms:
        where_clauses.append(f"duration > {input_data.min_duration_ms}")

    if input_data.url_filter:
        where_clauses.append(f'url contains "{input_data.url_filter}"')

    where_str = " and ".join(where_clauses) if where_clauses else "1==1"

    query = f"""
    requests
    | where {where_str}
    | order by timestamp desc
    | take {input_data.limit}
    | project timestamp, name, url, resultCode, duration, success,
              cloud_RoleName, operation_Id
    """

    return await _run_kusto_query(
        KustoQueryInput(query=query, timespan=input_data.timespan)
    )


async def _query_dependencies(input_data: DependenciesQueryInput) -> str:
    """Query external dependencies."""
    where_clauses = []

    if input_data.failed_only:
        where_clauses.append("success == false")

    if input_data.type_filter:
        where_clauses.append(f'type == "{input_data.type_filter}"')

    where_str = " and ".join(where_clauses) if where_clauses else "1==1"

    query = f"""
    dependencies
    | where {where_str}
    | order by timestamp desc
    | take {input_data.limit}
    | project timestamp, name, type, target, data, duration, success,
              resultCode, cloud_RoleName, operation_Id
    """

    return await _run_kusto_query(
        KustoQueryInput(query=query, timespan=input_data.timespan)
    )


async def _query_metrics(input_data: MetricsQueryInput) -> str:
    """Query Application Insights metrics."""
    credential = DefaultAzureCredential()
    client = MetricsQueryClient(credential)

    resource_id = _get_resource_id(input_data.resource_id)
    timespan = _parse_timespan(input_data.timespan)
    interval = _parse_timespan(input_data.interval)

    response = client.query_resource(
        resource_uri=resource_id,
        metric_names=[input_data.metric_name],
        timespan=timespan,
        granularity=interval,
        aggregations=[input_data.aggregation],
    )

    results = []
    for metric in response.metrics:
        for ts in metric.timeseries:
            for data in ts.data:
                value = getattr(data, input_data.aggregation, None)
                results.append(
                    {"timestamp": data.timestamp.isoformat(), "value": value}
                )

    return json.dumps(results, indent=2)


async def _query_availability(input_data: AvailabilityQueryInput) -> str:
    """Query availability test results."""
    where_clauses = []

    if input_data.test_name:
        where_clauses.append(f'name == "{input_data.test_name}"')

    if input_data.failed_only:
        where_clauses.append("success == false")

    where_str = " and ".join(where_clauses) if where_clauses else "1==1"

    query = f"""
    availabilityResults
    | where {where_str}
    | order by timestamp desc
    | take {input_data.limit}
    | project timestamp, name, location, success, duration, message
    """

    return await _run_kusto_query(
        KustoQueryInput(query=query, timespan=input_data.timespan)
    )
