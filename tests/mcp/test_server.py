"""Tests for MCP server initialization."""

from robocop.mcp import create_server, mcp


class TestServerInitialization:
    """Tests for MCP server setup."""

    def test_server_created(self):
        """Test that the server is created successfully."""
        assert mcp is not None
        assert mcp.name == "robocop"

    def test_create_server_returns_same_instance(self):
        """Test that create_server returns the singleton instance."""
        server = create_server()
        assert server is mcp
