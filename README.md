# 🐳 MCP Container Tools

[![PyPI version](https://img.shields.io/pypi/v/mcp-container-tools.svg)](https://pypi.org/project/mcp-container-tools/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A Model Context Protocol (MCP) server for Docker, Kubernetes, and Azure Application Insights with advanced log filtering and monitoring capabilities.

## ✨ Features

- 🐳 **Docker** — Container logs, inspect, exec, list containers
- 🐙 **Docker Compose** — Service logs, start/stop/restart services
- ☸️ **Kubernetes** — Pod logs, deployment logs, events, exec into pods
- ☁️ **Azure Application Insights** — Exceptions, traces, requests, metrics
- 🔍 **Log Filtering** — Filter by log level, regex patterns, exclude patterns
- 🌐 **Remote Support** — Connect to remote Docker hosts via SSH or TCP

## 📋 Requirements

| Requirement | Version | Required For |
|-------------|---------|--------------|
| 🐍 Python | 3.11+ | All |
| 🐳 Docker | Latest | Docker tools |
| ☸️ kubectl | Latest | Kubernetes tools |
| ☁️ Azure CLI | Latest | Azure tools (optional) |

## 🚀 Installation

### 📦 Quick Install (recommended)

```bash
# Basic installation
pip install mcp-container-tools

# With Azure Application Insights support
pip install mcp-container-tools[azure]
```

### 🐙 Install from GitHub

```bash
# Latest version from GitHub
pip install git+https://github.com/simseksem/mcp-container-tools.git

# With Azure support
pip install "mcp-container-tools[azure] @ git+https://github.com/simseksem/mcp-container-tools.git"
```

### 🔧 Install from source (for development)

```bash
git clone https://github.com/simseksem/mcp-container-tools.git
cd mcp-container-tools
pip install -e ".[all]"
```

### ✅ Verify installation

```bash
mcp-server --help
```

## ⚙️ Configuration

### 🖥️ Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "container-tools": {
      "command": "/path/to/mcp-container-tools/.venv/bin/python",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "AZURE_LOG_ANALYTICS_WORKSPACE_ID": "your-workspace-id",
        "AZURE_APP_INSIGHTS_RESOURCE_ID": "/subscriptions/.../resourceGroups/.../providers/microsoft.insights/components/..."
      }
    }
  }
}
```

### 💻 Claude Code

Add to `~/.claude/settings.json` or create `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "container-tools": {
      "command": "/path/to/mcp-container-tools/.venv/bin/python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

### ☁️ Azure Authentication

Azure tools use `DefaultAzureCredential` which supports:
- Azure CLI (`az login`)
- Environment variables
- Managed Identity
- Visual Studio Code

```bash
# Easiest: Login with Azure CLI
az login
```

## 📖 Usage Examples

### 🐳 Docker

```python
# Read container logs
docker_logs(container="my-app", tail=100)

# Read logs from last 30 minutes
docker_logs(container="my-app", since="30m")

# Filter by log level (only errors and above)
docker_logs(container="my-app", min_level="error")

# Search for patterns
docker_logs(container="my-app", pattern="timeout|connection refused")

# Exclude health checks
docker_logs(container="my-app", exclude_pattern="GET /health")

# Remote Docker host via SSH
docker_logs(container="my-app", host="ssh://user@server.com")

# List containers
docker_ps(all=True)
```

### 🐙 Docker Compose

```python
# Read service logs
compose_logs(service="api", tail=200)

# Read all services logs
compose_logs(project_dir="/path/to/project")

# Service management
compose_up(service="api", project_dir="/path/to/project")
compose_down(project_dir="/path/to/project")
compose_restart(service="api")
```

### ☸️ Kubernetes

```python
# Read pod logs
k8s_logs(pod="api-7d4b8c6f9-x2k4m", namespace="production")

# Read logs from all pods in a deployment
k8s_deployment_logs(deployment="api", namespace="production")

# Filter logs
k8s_logs(pod="api-*", min_level="warn", pattern="database")

# Use different context
k8s_logs(pod="my-pod", context="production-cluster", namespace="backend")

# List pods
k8s_pods(namespace="all", selector="app=api")

# Get events
k8s_events(namespace="production")

# Execute command in pod
k8s_exec(pod="api-xyz", command="printenv", namespace="production")
```

### ☁️ Azure Application Insights

```python
# Query exceptions from last hour
azure_exceptions(timespan="PT1H", limit=50)

# Get only critical exceptions
azure_exceptions(severity="critical", search="NullReference")

# Query application traces
azure_traces(timespan="PT1H", severity="error")

# Query HTTP requests
azure_requests(timespan="PT1H", failed_only=True)

# Get slow requests (>1 second)
azure_requests(min_duration_ms=1000, limit=20)

# Query external dependencies (SQL, HTTP, etc.)
azure_dependencies(timespan="PT1H", failed_only=True, type_filter="SQL")

# Get metrics
azure_metrics(metric_name="requests/count", timespan="P1D", interval="PT1H")

# Query availability test results
azure_availability(timespan="P1D", failed_only=True)

# Run custom Kusto query
azure_query(query="""
    requests
    | where success == false
    | summarize count() by bin(timestamp, 1h), resultCode
    | order by timestamp desc
""", timespan="P1D")
```

### 🔍 Log Filtering Options

All log tools support these filtering options:

| Option | Description | Example |
|--------|-------------|---------|
| `min_level` | Minimum log level | `"error"`, `"warn"`, `"info"` |
| `pattern` | Regex to include | `"error\|exception"` |
| `exclude_pattern` | Regex to exclude | `"health.*check"` |
| `context_lines` | Lines around matches | `5` |

**Supported log levels:** `trace` → `debug` → `info` → `warn` → `error` → `fatal`

### ⏱️ Timespan Format (Azure)

Azure tools use ISO 8601 duration format:

| Format | Duration |
|--------|----------|
| `PT1H` | 1 hour |
| `PT30M` | 30 minutes |
| `P1D` | 1 day |
| `P7D` | 7 days |

## 🛠️ Available Tools

### 🐳 Docker Tools
| Tool | Description |
|------|-------------|
| `docker_logs` | 📄 Read container logs with filtering |
| `docker_ps` | 📋 List containers |
| `docker_inspect` | 🔎 Get container details |
| `docker_exec` | ⚡ Execute command in container |

### 🐙 Docker Compose Tools
| Tool | Description |
|------|-------------|
| `compose_logs` | 📄 Read service logs |
| `compose_ps` | 📋 List services |
| `compose_up` | ▶️ Start services |
| `compose_down` | ⏹️ Stop services |
| `compose_restart` | 🔄 Restart services |

### ☸️ Kubernetes Tools
| Tool | Description |
|------|-------------|
| `k8s_logs` | 📄 Read pod logs |
| `k8s_deployment_logs` | 📚 Read deployment logs |
| `k8s_pods` | 📋 List pods |
| `k8s_describe` | 🔎 Describe pod |
| `k8s_exec` | ⚡ Execute in pod |
| `k8s_events` | 📢 Get events |
| `k8s_contexts` | 🌐 List contexts |

### ☁️ Azure Application Insights Tools
| Tool | Description |
|------|-------------|
| `azure_query` | 🔍 Run custom Kusto queries |
| `azure_exceptions` | ❌ Query application exceptions |
| `azure_traces` | 📝 Query application traces |
| `azure_requests` | 🌐 Query HTTP requests |
| `azure_dependencies` | 🔗 Query external dependencies |
| `azure_metrics` | 📊 Query metrics |
| `azure_availability` | ✅ Query availability tests |

## 👨‍💻 Development

### Install dev dependencies

```bash
pip install -e ".[all]"
```

### Run tests

```bash
pytest
```

### Linting and type checking

```bash
ruff check .
mypy src/
```

## 📁 Project Structure

```
mcp-container-tools/
├── 📂 src/mcp_server/
│   ├── 📄 __init__.py
│   ├── 📄 server.py               # Main server entry point
│   ├── 📂 tools/
│   │   ├── 🐳 docker.py           # Docker tools
│   │   ├── 🐙 docker_compose.py   # Compose tools
│   │   ├── ☸️ kubernetes.py        # K8s tools
│   │   ├── ☁️ azure_insights.py    # Azure App Insights
│   │   └── 📁 file_operations.py  # File tools
│   ├── 📂 resources/
│   │   ├── ⚙️ config.py           # Config resources
│   │   └── 📊 data.py             # Data resources
│   ├── 📂 prompts/
│   │   └── 📝 templates.py        # Prompt templates
│   └── 📂 utils/
│       └── 🔍 log_filter.py       # Log filtering
├── 📂 tests/
├── 📄 pyproject.toml
└── 📄 README.md
```

## 🔐 Environment Variables

| Variable | Description |
|----------|-------------|
| `AZURE_LOG_ANALYTICS_WORKSPACE_ID` | Azure Log Analytics workspace ID |
| `AZURE_APP_INSIGHTS_RESOURCE_ID` | Azure Application Insights resource ID |

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

<p align="center">
  Made with ❤️ for the MCP community
</p>
