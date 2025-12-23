"""Pytest configuration for MCP tests."""

import sys

# Skip all tests in this directory if Python < 3.10 or fastmcp not installed
collect_ignore_glob = []

if sys.version_info < (3, 10):
    collect_ignore_glob.append("test_*.py")
else:
    try:
        import fastmcp  # noqa: F401
    except ImportError:
        collect_ignore_glob.append("test_*.py")
