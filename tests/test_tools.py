"""Tests for MCP tools."""

import pytest

from mcp_server.tools.calculator import CalculateInput, _perform_calculation


class TestCalculator:
    """Tests for calculator tool."""

    def test_add(self):
        input_data = CalculateInput(operation="add", a=2, b=3)
        assert _perform_calculation(input_data) == 5

    def test_subtract(self):
        input_data = CalculateInput(operation="subtract", a=10, b=4)
        assert _perform_calculation(input_data) == 6

    def test_multiply(self):
        input_data = CalculateInput(operation="multiply", a=3, b=4)
        assert _perform_calculation(input_data) == 12

    def test_divide(self):
        input_data = CalculateInput(operation="divide", a=10, b=2)
        assert _perform_calculation(input_data) == 5

    def test_divide_by_zero(self):
        input_data = CalculateInput(operation="divide", a=10, b=0)
        assert _perform_calculation(input_data) == float("inf")

    def test_unknown_operation(self):
        input_data = CalculateInput(operation="power", a=2, b=3)
        with pytest.raises(ValueError, match="Unknown operation"):
            _perform_calculation(input_data)
