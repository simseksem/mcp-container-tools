"""Tests for MCP tools."""

import pytest

from mcp_server.utils.log_filter import filter_logs, LogLevel


class TestLogFilter:
    """Tests for log filtering."""

    def test_filter_by_level_error(self):
        logs = "INFO ok\nERROR fail\nWARN warning"
        result = filter_logs(logs, min_level="error")
        assert "ERROR fail" in result
        assert "INFO ok" not in result

    def test_filter_by_pattern(self):
        logs = "INFO starting\nERROR database failed\nINFO done"
        result = filter_logs(logs, pattern="database")
        assert "database" in result
        assert "starting" not in result

    def test_filter_exclude_pattern(self):
        logs = "INFO health check\nERROR real error\nINFO health check"
        result = filter_logs(logs, exclude_pattern="health")
        assert "real error" in result
        assert "health" not in result

    def test_filter_combined(self):
        logs = "DEBUG test\nERROR db failed\nERROR health check failed"
        result = filter_logs(logs, min_level="error", exclude_pattern="health")
        assert "db failed" in result
        assert "health" not in result
        assert "DEBUG" not in result
