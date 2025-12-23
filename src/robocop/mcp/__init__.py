"""
Robocop MCP Server - Expose linting and formatting via Model Context Protocol.

This module provides an MCP server that allows AI assistants to lint and format
Robot Framework code directly.

Install with: pip install robotframework-robocop[mcp]
Run with: robocop-mcp
"""

try:
    from robocop.mcp.server import create_server, main, mcp
except ImportError as e:
    raise ImportError("MCP dependencies not installed. Install with: pip install robotframework-robocop[mcp]") from e

__all__ = ["create_server", "main", "mcp"]
