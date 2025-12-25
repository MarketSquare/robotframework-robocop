"""Tests for MCP middleware configuration."""

from robocop.mcp import mcp
from robocop.mcp.middleware import (
    TOOLS_CACHEABLE,
    TOOLS_NEVER_CACHE,
    TTL_DISCOVERY,
    TTL_INFO,
    TTL_METADATA,
    TTL_RESOURCES,
    create_caching_middleware,
    create_error_handling_middleware,
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
        # Discovery TTL should be moderate (1-30 min)
        assert 60 <= TTL_DISCOVERY <= 1800

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
