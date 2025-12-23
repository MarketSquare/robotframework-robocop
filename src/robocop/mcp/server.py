"""Robocop MCP Server - FastMCP-based server exposing linting and formatting tools."""

from __future__ import annotations

from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(
    name="robocop",
    instructions="""
Robocop is a linter and formatter for Robot Framework code. It helps maintain
code quality by identifying issues and automatically fixing style problems.

## Quick Start

1. **Lint code**: Use `lint_content` for inline code or `lint_file` for files
2. **Format code**: Use `format_content` to auto-fix style issues
3. **Combined**: Use `lint_and_format` to format and show remaining issues

## Available Tools

### Linting Tools
- `lint_content`: Lint Robot Framework code provided as text
- `lint_file`: Lint a single .robot or .resource file
- `lint_files`: Lint multiple files by path or glob pattern
- `lint_directory`: Lint all Robot Framework files in a directory
- `suggest_fixes`: Get actionable fix suggestions for issues

### Formatting Tools
- `format_content`: Auto-format Robot Framework code
- `lint_and_format`: Format code and report remaining issues

### Discovery Tools
- `list_rules`: List available linting rules (with filtering)
- `list_formatters`: List available formatters
- `get_rule_info`: Get detailed documentation for a rule
- `get_formatter_info`: Get detailed documentation for a formatter

## Severity Levels

Issues are returned with severity levels:
- **E (Error)**: Critical issues that likely cause test failures
- **W (Warning)**: Issues that should be fixed but won't break tests
- **I (Info)**: Style suggestions and best practices

## Common Workflows

### Review Code Quality
1. Use `lint_content` or `lint_file` to identify issues
2. Use `suggest_fixes` to get fix recommendations
3. Apply fixes and re-lint to verify

### Clean Up Code
1. Use `lint_and_format` to auto-fix and see remaining issues
2. Address manual fixes based on suggestions
3. Verify with final lint

### Configure for a Project
1. Use `list_rules` to explore available rules
2. Use the `configure_robocop` prompt for recommendations
3. Apply settings to your `.robocop` configuration file

## Rule Configuration

Rules can be configured using the `configure` parameter:
- `configure=["line-too-long.line_length=140"]` - Set max line length
- `configure=["too-long-keyword.max_len=50"]` - Set max keyword length

Use `get_rule_info` to see configurable parameters for any rule.

## Managing Large Result Sets

When linting many files, use `group_by` to organize results for easier processing:

- `group_by="severity"` - Prioritize fixes: see all errors first, then warnings, then info
- `group_by="rule"` - Batch fixes: group same rule violations together
- `group_by="file"` - File review: see all issues per file

When `group_by` is set, `limit` applies per group (e.g., `limit=5, group_by="rule"`
shows up to 5 examples per rule).

Example:
    lint_files(["tests/**/*.robot"], group_by="severity", limit=10)
    # Returns: {"issues": {"E": [...], "W": [...], "I": [...]}, "group_counts": {...}}
""",
)


def _register_all() -> None:
    """Register all tools, resources, prompts, and middleware with the MCP server."""
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
        FastMCP: The MCP server instance.

    """
    return mcp


def main() -> None:
    """Entry point for the robocop-mcp command."""
    mcp.run()


if __name__ == "__main__":
    main()
