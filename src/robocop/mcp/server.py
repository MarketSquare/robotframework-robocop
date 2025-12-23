"""Robocop MCP Server - FastMCP-based server exposing linting and formatting tools."""

from __future__ import annotations

from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(
    name="robocop",
    instructions="""
Robocop is a linter and formatter for Robot Framework code.

Use these tools to:
- Lint Robot Framework files to find issues and style violations
- Format Robot Framework code to follow consistent style
- Get information about available rules and formatters

When linting, issues are returned with severity levels:
- E (Error): Critical issues that likely cause test failures
- W (Warning): Issues that should be fixed but won't break tests
- I (Info): Style suggestions and best practices
""",
)


def _register_all() -> None:
    """Register all tools, resources, and prompts with the MCP server."""
    from robocop.mcp.prompts import register_prompts
    from robocop.mcp.resources import register_resources
    from robocop.mcp.tools import register_tools

    register_tools(mcp)
    register_resources(mcp)
    register_prompts(mcp)


# Register everything at module load time
_register_all()


def create_server() -> FastMCP:
    """
    Create and return the MCP server instance.

    Returns:
        FastMCP: The MCP server instance.'

    """
    return mcp


def main() -> None:
    """Entry point for the robocop-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
