"""Robocop MCP Server - FastMCP-based server exposing linting and formatting tools."""

from __future__ import annotations

from fastmcp import FastMCP

# Create the MCP server instance
mcp = FastMCP(
    name="robocop",
    instructions="""
Robocop is a linter and formatter for Robot Framework code. Use it to identify
issues, auto-fix style problems, and measure code quality.

## Quick Start

- **Check code**: `lint_content` (inline) or `lint_file` / `lint_files` (from disk)
- **Format code**: `format_content` (inline) or `format_file` / `format_files` (from disk)
- **Understand issues**: `explain_issue` for detailed context, `get_rule_info` for rule docs
- **Assess quality**: `get_statistics` for codebase-wide metrics and quality score

## Tools by Category

### Linting (identify issues)
| Tool | Use When |
|------|----------|
| `lint_content` | Checking code provided as text |
| `lint_file` | Checking a single file on disk |
| `lint_files` | Checking multiple files by path or glob pattern |
| `lint_directory` | Checking all files in a directory |
| `suggest_fixes` | Getting actionable fix recommendations |
| `explain_issue` | Understanding why a specific line is flagged |

### Formatting (auto-fix style)
| Tool | Use When |
|------|----------|
| `format_content` | Formatting code provided as text |
| `format_file` | Formatting a single file (optionally overwrite) |
| `format_files` | Formatting multiple files by glob pattern |
| `lint_and_format` | Formatting + showing remaining manual fixes |

### Discovery (explore rules/formatters)
| Tool | Use When |
|------|----------|
| `list_rules` | Finding available rules (supports filtering) |
| `list_formatters` | Finding available formatters |
| `get_rule_info` | Getting documentation for a specific rule |
| `get_formatter_info` | Getting documentation for a specific formatter |

### Statistics (measure quality)
| Tool | Use When |
|------|----------|
| `get_statistics` | Getting quality score, common issues, recommendations |

## Severity Levels

- **E (Error)**: Critical issues that may cause test failures
- **W (Warning)**: Issues that should be fixed but won't break tests
- **I (Info)**: Style suggestions and best practices

## Common Workflows

### Quick Code Review
1. `lint_content` or `lint_file` to identify issues
2. `explain_issue` for any confusing violations
3. Apply fixes based on suggestions

### Clean Up Files
1. `format_file` with `overwrite=True` to auto-fix style
2. `lint_file` to see remaining issues
3. Fix manually and verify

### Assess Codebase Health
1. `get_statistics` for quality score and top issues
2. Focus on errors first, then most common warnings
3. Use formatter to batch-fix style issues

### Configure Rules
Rules accept configuration via `configure` parameter:
```
configure=["line-too-long.line_length=140", "too-long-keyword.max_len=50"]
```
Use `get_rule_info` to see configurable parameters.

## Handling Large Result Sets

Use `group_by` to organize results:
- `group_by="severity"` - Errors first, then warnings, then info
- `group_by="rule"` - Same violations grouped together
- `group_by="file"` - All issues per file

With `group_by`, `limit` applies per group.
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
