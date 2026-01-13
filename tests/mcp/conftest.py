"""Pytest configuration for MCP tests."""

# Skip all tests in this directory if fastmcp not installed
collect_ignore_glob = []

try:
    import fastmcp  # noqa: F401
except ImportError:
    collect_ignore_glob.append("test_*.py")
