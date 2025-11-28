# MCP Server - Docker & Kubernetes Logs

A Model Context Protocol (MCP) server for reading and managing Docker, Docker Compose, and Kubernetes logs with advanced filtering capabilities.

## Features

- **Docker**: Container logs, inspect, exec, list containers
- **Docker Compose**: Service logs, start/stop/restart services
- **Kubernetes**: Pod logs, deployment logs, events, exec into pods
- **Log Filtering**: Filter by log level, regex patterns, exclude patterns
- **Remote Support**: Connect to remote Docker hosts via SSH or TCP

## Requirements

- Python 3.11+
- Docker (for Docker tools)
- kubectl (for Kubernetes tools)

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/mcp-docker-server.git
cd mcp-docker-server
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# or
.venv\Scripts\activate  # Windows
```

### 3. Install the package

```bash
pip install -e .
```

### 4. Verify installation

```bash
mcp-server --help
# or
python -m mcp_server.server
```

## Configuration

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "docker-server": {
      "command": "/path/to/python-mcp-server/.venv/bin/python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

### Claude Code

Add to `~/.claude/settings.json` or create `.mcp.json` in your project:

```json
{
  "mcpServers": {
    "docker-server": {
      "command": "/path/to/python-mcp-server/.venv/bin/python",
      "args": ["-m", "mcp_server.server"]
    }
  }
}
```

## Usage Examples

### Docker

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

### Docker Compose

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

### Kubernetes

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

### Log Filtering Options

All log tools support these filtering options:

| Option | Description | Example |
|--------|-------------|---------|
| `min_level` | Minimum log level | `"error"`, `"warn"`, `"info"` |
| `pattern` | Regex to include | `"error\|exception"` |
| `exclude_pattern` | Regex to exclude | `"health.*check"` |
| `context_lines` | Lines around matches | `5` |

Supported log levels: `trace`, `debug`, `info`, `warn`, `error`, `fatal`

## Available Tools

### Docker Tools
| Tool | Description |
|------|-------------|
| `docker_logs` | Read container logs with filtering |
| `docker_ps` | List containers |
| `docker_inspect` | Get container details |
| `docker_exec` | Execute command in container |

### Docker Compose Tools
| Tool | Description |
|------|-------------|
| `compose_logs` | Read service logs |
| `compose_ps` | List services |
| `compose_up` | Start services |
| `compose_down` | Stop services |
| `compose_restart` | Restart services |

### Kubernetes Tools
| Tool | Description |
|------|-------------|
| `k8s_logs` | Read pod logs |
| `k8s_deployment_logs` | Read deployment logs |
| `k8s_pods` | List pods |
| `k8s_describe` | Describe pod |
| `k8s_exec` | Execute in pod |
| `k8s_events` | Get events |
| `k8s_contexts` | List contexts |

## Development

### Install dev dependencies

```bash
pip install -e ".[dev]"
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

## Project Structure

```
python-mcp-server/
├── src/mcp_server/
│   ├── __init__.py
│   ├── server.py              # Main server entry point
│   ├── tools/
│   │   ├── docker.py          # Docker tools
│   │   ├── docker_compose.py  # Compose tools
│   │   ├── kubernetes.py      # K8s tools
│   │   ├── calculator.py      # Example tool
│   │   └── file_operations.py # File tools
│   ├── resources/
│   │   ├── config.py          # Config resources
│   │   └── data.py            # Data resources
│   ├── prompts/
│   │   └── templates.py       # Prompt templates
│   └── utils/
│       └── log_filter.py      # Log filtering
├── tests/
├── pyproject.toml
└── README.md
```

## License

MIT
