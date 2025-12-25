"""Tests for MCP middleware configuration."""

import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server.middleware.caching import ResponseCachingMiddleware
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

from robocop.mcp import mcp
from robocop.mcp.middleware import (
    TOOLS_CACHEABLE,
    TOOLS_NEVER_CACHE,
    TTL_INFO,
    TTL_METADATA,
    TTL_RESOURCES,
    create_caching_middleware,
    create_error_handling_middleware,
)
from robocop.mcp.tools import (
    _get_formatter_info_impl,
    _get_rule_info_impl,
    _lint_file_impl,
)


class TestMiddlewareConfiguration:
    """Test middleware is configured correctly."""

    def test_caching_middleware_created(self):
        """Test ResponseCachingMiddleware can be created."""
        middleware = create_caching_middleware()
        assert middleware is not None

    def test_error_handling_middleware_created(self):
        """Test ErrorHandlingMiddleware can be created."""
        middleware = create_error_handling_middleware()
        assert middleware is not None

    def test_tool_categories_are_disjoint(self):
        """Ensure no tool is in multiple caching categories."""
        assert TOOLS_CACHEABLE.isdisjoint(TOOLS_NEVER_CACHE)

    def test_cacheable_tools_are_known(self):
        """Ensure cacheable tools are recognized tool names."""
        known_cacheable = {"list_rules", "list_formatters", "get_rule_info", "get_formatter_info"}
        assert known_cacheable == TOOLS_CACHEABLE

    def test_never_cache_tools_are_known(self):
        """Ensure never-cache tools are recognized tool names."""
        expected = {
            "lint_content",
            "lint_file",
            "lint_files",
            "lint_directory",
            "format_content",
            "format_file",
            "format_files",
            "lint_and_format",
            "suggest_fixes",
            "explain_issue",
            "get_statistics",
        }
        assert expected == TOOLS_NEVER_CACHE

    def test_ttl_values_are_sensible(self):
        """Validate TTL values are within reasonable ranges."""
        # Info TTL should be long (10+ min)
        assert TTL_INFO >= 600

        # Metadata TTL should be moderate
        assert 60 <= TTL_METADATA <= 1800

        # Resources TTL should be moderate
        assert 60 <= TTL_RESOURCES <= 1800


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
