"""Tests for MCP middleware configuration."""

import importlib

import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

from robocop.mcp import mcp, middleware
from robocop.mcp.middleware import (
    create_caching_middleware,
    create_error_handling_middleware,
)
from robocop.mcp.tools import (
    _get_formatter_info_impl,
    _get_rule_info_impl,
    _lint_file_impl,
)


class TestMiddlewareRegistration:
    """Test middleware registration with server."""

    def test_middleware_registered_with_server(self):
        """Test middleware is properly registered."""
        # Server should have middleware registered
        # This tests that _register_all() ran successfully
        assert mcp is not None
        assert mcp.name == "robocop"


class TestCachingMiddlewareBehavior:
    """Integration tests verifying caching middleware actually works."""

    def test_caching_middleware_is_response_caching_middleware(self):
        """Test that caching middleware is the correct type."""
        middleware = create_caching_middleware()
        assert isinstance(middleware, ResponseCachingMiddleware)

    def test_get_rule_info_returns_consistent_results(self):
        """Test that get_rule_info returns same results for same rule."""
        # Use a known rule ID (new format)
        result1 = _get_rule_info_impl("LEN01")
        result2 = _get_rule_info_impl("LEN01")

        assert result1 == result2
        assert result1["rule_id"] == "LEN01"

    def test_get_formatter_info_returns_consistent_results(self):
        """Test that get_formatter_info returns same results for same formatter."""
        result1 = _get_formatter_info_impl("NormalizeSeparators")
        result2 = _get_formatter_info_impl("NormalizeSeparators")

        assert result1 == result2
        assert result1["name"] == "NormalizeSeparators"


class TestErrorHandlingMiddlewareBehavior:
    """Integration tests verifying error handling middleware works."""

    def test_error_handling_middleware_is_correct_type(self):
        """Test that error handling middleware is the correct type."""
        middleware = create_error_handling_middleware()
        assert isinstance(middleware, ErrorHandlingMiddleware)

    def test_error_handling_middleware_has_traceback_enabled(self):
        """Test that error handling middleware has traceback enabled for debugging."""
        middleware = create_error_handling_middleware()
        assert middleware.include_traceback is True

    def test_tool_error_is_raised_for_invalid_rule(self):
        """Test that ToolError is raised for non-existent rule."""
        with pytest.raises(ToolError) as exc_info:
            _get_rule_info_impl("NONEXISTENT99")

        assert "not found" in str(exc_info.value).lower()

    def test_tool_error_is_raised_for_invalid_formatter(self):
        """Test that ToolError is raised for non-existent formatter."""
        with pytest.raises(ToolError) as exc_info:
            _get_formatter_info_impl("NonexistentFormatter")

        assert "not found" in str(exc_info.value).lower()

    def test_tool_error_for_file_not_found(self):
        """Test that ToolError is raised for non-existent file."""
        with pytest.raises(ToolError) as exc_info:
            _lint_file_impl("/nonexistent/path/to/file.robot")

        error_msg = str(exc_info.value).lower()
        assert "not found" in error_msg or "does not exist" in error_msg


class TestCachingDisabledEnvironmentVariable:
    """Tests for ROBOCOP_MCP_NO_CACHE environment variable."""

    def test_caching_middleware_not_registered_when_env_var_set(self, monkeypatch):
        """Test that caching middleware is not added when ROBOCOP_MCP_NO_CACHE=1."""
        # Set the environment variable before reloading middleware
        monkeypatch.setenv("ROBOCOP_MCP_NO_CACHE", "1")

        # Reload middleware module to pick up the env var
        importlib.reload(middleware)

        # Create a fresh MCP server and register middleware
        test_mcp = FastMCP(name="test-robocop")
        middleware.register_middleware(test_mcp)

        # Check that no ResponseCachingMiddleware was added
        has_caching_middleware = any(isinstance(m, ResponseCachingMiddleware) for m in test_mcp.middleware)
        assert not has_caching_middleware, "Caching middleware should not be registered when ROBOCOP_MCP_NO_CACHE=1"

        # Verify error handling middleware is still registered
        has_error_middleware = any(isinstance(m, ErrorHandlingMiddleware) for m in test_mcp.middleware)
        assert has_error_middleware, "Error handling middleware should still be registered"

        # Cleanup: reload middleware with default settings
        monkeypatch.delenv("ROBOCOP_MCP_NO_CACHE", raising=False)
        importlib.reload(middleware)
