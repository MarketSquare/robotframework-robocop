"""
FastMCP Middleware configuration for Robocop MCP server.

This module configures caching and error handling middleware to reduce
LLM token usage and improve robustness.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastmcp.server.middleware.caching import (
    CallToolSettings,
    ListPromptsSettings,
    ListResourcesSettings,
    ListToolsSettings,
    ReadResourceSettings,
    ResponseCachingMiddleware,
)
from fastmcp.server.middleware.error_handling import ErrorHandlingMiddleware

if TYPE_CHECKING:
    from fastmcp import FastMCP

# Logger for MCP middleware
logger = logging.getLogger("robocop.mcp")

# === TTL Constants (in seconds) ===

# Discovery/catalog operations - long TTL, data is static during session
TTL_DISCOVERY = 600  # 10 minutes

# Rule/formatter info - very long TTL, documentation doesn't change
TTL_INFO = 1800  # 30 minutes

# MCP metadata (list tools/resources/prompts) - long TTL
TTL_METADATA = 600  # 10 minutes

# Resource TTL (rules/formatters catalogs)
TTL_RESOURCES = 600  # 10 minutes


# === Tool Categories for Caching ===

# Tools that CAN be cached - static discovery/documentation
TOOLS_CACHEABLE: frozenset[str] = frozenset(
    {
        "list_rules",  # Rule catalog is static
        "list_formatters",  # Formatter catalog is static
        "get_rule_info",  # Rule documentation is static
        "get_formatter_info",  # Formatter documentation is static
    }
)

# Tools that should NEVER be cached (depend on file content that changes)
# Not used in middleware config, but documented for reference
TOOLS_NEVER_CACHE: frozenset[str] = frozenset(
    {
        "lint_content",  # Content changes between calls
        "lint_file",  # File content may change
        "lint_files",  # Files may change
        "lint_directory",  # Directory contents may change
        "format_content",  # Content changes between calls
        "format_file",  # File content may change (also writes!)
        "format_files",  # Files may change (also writes!)
        "lint_and_format",  # Content changes between calls
        "suggest_fixes",  # Depends on content parameter
        "explain_issue",  # Depends on content parameter
        "get_statistics",  # May change as files are edited
    }
)


def create_caching_middleware() -> ResponseCachingMiddleware:
    """
    Create ResponseCachingMiddleware with optimized settings for Robocop.

    Caching Strategy:
    - Discovery tools (list_*): Long TTL (10 min) - rules/formatters don't change
    - Info tools (get_*_info): Long TTL (30 min) - documentation is static
    - Linting/Formatting: Never cache - depends on file content
    - MCP metadata: Long TTL (10 min) - tool/resource lists are static

    Returns:
        ResponseCachingMiddleware configured for Robocop tools.

    """
    return ResponseCachingMiddleware(
        # List tools - cache metadata about available tools
        list_tools_settings=ListToolsSettings(
            ttl=TTL_METADATA,
            enabled=True,
        ),
        # List resources - cache metadata about available resources
        list_resources_settings=ListResourcesSettings(
            ttl=TTL_METADATA,
            enabled=True,
        ),
        # List prompts - cache metadata about available prompts
        list_prompts_settings=ListPromptsSettings(
            ttl=TTL_METADATA,
            enabled=True,
        ),
        # Call tool - selective caching based on tool name
        call_tool_settings=CallToolSettings(
            # Only cache discovery and info tools
            included_tools=list(TOOLS_CACHEABLE),
            ttl=TTL_INFO,  # Default TTL for cacheable tools
            enabled=True,
        ),
        # Read resource - cache rules/formatters catalogs
        read_resource_settings=ReadResourceSettings(
            ttl=TTL_RESOURCES,
            enabled=True,
        ),
    )


def create_error_handling_middleware() -> ErrorHandlingMiddleware:
    """
    Create ErrorHandlingMiddleware with appropriate settings for Robocop.

    Error Handling Strategy:
    - Log all errors for debugging
    - Transform exceptions to MCP-compliant error responses
    - Don't expose tracebacks to LLMs (security/clarity)

    Returns:
        ErrorHandlingMiddleware configured for Robocop.

    """
    return ErrorHandlingMiddleware(
        logger=logger,
        include_traceback=False,  # Don't expose internals to LLMs
    )


def register_middleware(mcp: FastMCP) -> None:
    """
    Register all middleware with the MCP server.

    Middleware Order (first to last):
    1. ErrorHandlingMiddleware - Catches and transforms all errors
    2. ResponseCachingMiddleware - Caches responses after error handling

    This order ensures:
    - Errors are properly caught and logged before caching
    - Error responses are NOT cached (only successful responses)
    - Cache hits bypass error handling (already validated)

    Args:
        mcp: The FastMCP server instance.

    """
    # 1. Error handling first - catches errors from all downstream middleware
    mcp.add_middleware(create_error_handling_middleware())

    # 2. Caching second - caches successful responses
    mcp.add_middleware(create_caching_middleware())
