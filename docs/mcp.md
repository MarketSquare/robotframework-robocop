# MCP Server

Robocop provides an MCP (Model Context Protocol) server that allows AI assistants to lint and format Robot Framework code directly.

## Installation

Install Robocop with MCP support:

```bash
pip install robotframework-robocop[mcp]
```

!!! note "Python Version Requirement"
    MCP support requires Python 3.10 or higher. The core Robocop functionality still supports Python 3.9+.

## Running the Server

### Standalone

```bash
robocop-mcp
```

### With Claude Desktop

Add to your Claude Desktop configuration (`~/.config/claude-desktop/config.json` on Linux, `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "robocop": {
      "command": "robocop-mcp"
    }
  }
}
```

### With uvx (Recommended)

Using uvx ensures you always have the latest version:

```json
{
  "mcpServers": {
    "robocop": {
      "command": "uvx",
      "args": ["--from", "robotframework-robocop[mcp]", "robocop-mcp"]
    }
  }
}
```

### With VS Code

For VS Code extensions that support MCP, add to your settings:

```json
{
  "mcp.servers": {
    "robocop": {
      "command": "robocop-mcp",
      "transport": "stdio"
    }
  }
}
```

## Available Tools

### lint_content

Lint Robot Framework code provided as text content.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `content` | string | Robot Framework source code to lint |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: I, W, or E |

**Returns:** List of diagnostic issues with rule_id, name, message, severity, line, column, end_line, end_column.

**Tags:** `linting`

### lint_file

Lint a Robot Framework file from disk.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `file_path` | string | Absolute path to .robot or .resource file |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: I, W, or E |

**Returns:** List of diagnostic issues (same format as lint_content).

**Tags:** `linting`

### lint_directory

Lint all Robot Framework files in a directory.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `directory_path` | string | Absolute path to directory containing .robot/.resource files |
| `recursive` | bool | Whether to search subdirectories (default: true) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: I, W, or E |

**Returns:** Dictionary with `total_files`, `total_issues`, `files_with_issues`, `issues` (list with file paths), and `summary` (issues by severity).

**Tags:** `linting`

### format_content

Format Robot Framework code and return the formatted result.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `content` | string | Robot Framework source code to format |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `select` | list[str] | Formatter names to apply |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |

**Returns:** Dictionary with `formatted` (formatted code), `changed` (boolean), and `diff` (unified diff if changed).

**Tags:** `formatting`

### lint_and_format

Format Robot Framework code and lint the result in one operation. This is the recommended tool for cleaning up code.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `content` | string | Robot Framework source code to process |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `lint_select` | list[str] | Linter rule IDs/names to enable |
| `lint_ignore` | list[str] | Linter rule IDs/names to ignore |
| `threshold` | string | Minimum severity: I, W, or E |
| `format_select` | list[str] | Formatter names to apply |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |

**Returns:** Dictionary with `formatted`, `changed`, `diff`, `issues` (remaining issues), `issues_before`, `issues_after`, and `issues_fixed`.

**Tags:** `linting`, `formatting`

### get_rule_info

Get detailed documentation for a linting rule.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `rule_name_or_id` | string | Rule name or ID (e.g., "too-long-keyword" or "LEN01") |

**Returns:** Dictionary with rule details including documentation and configurable parameters.

**Tags:** `documentation`

### get_formatter_info

Get detailed documentation for a formatter.

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `formatter_name` | string | Formatter name (e.g., "NormalizeSeparators") |

**Returns:** Dictionary with formatter details including documentation.

**Tags:** `documentation`

## Available Resources

Resources provide read-only context data.

### robocop://rules

Complete catalog of all available linting rules with basic information.

### robocop://formatters

Complete catalog of all available formatters.

### robocop://rules/{rule_id}

Detailed information about a specific rule, including full documentation and parameters.

## Available Prompts

Prompts provide reusable templates for common operations.

### analyze_robot_file

Template for comprehensive Robot Framework code analysis.

**Arguments:**

- `content`: The Robot Framework code to analyze
- `focus`: Analysis focus ("all", "style", "errors", "best-practices")

### fix_robot_issues

Template for fixing all issues in Robot Framework code.

**Arguments:**

- `content`: The Robot Framework code to fix

### explain_rule

Template for explaining a Robocop rule with examples.

**Arguments:**

- `rule_name_or_id`: The rule to explain
- `code_snippet`: Optional code that triggered the rule

## Example Usage

When using Claude or another AI assistant with MCP support:

**Analyze code:**
> "Please analyze this Robot Framework code for issues:
> ```robot
> *** Test Cases ***
> test without capital
>     log  hello
> ```"

**Get rule information:**
> "What does the LEN01 rule check for?"

**Format code:**
> "Format this Robot Framework code using Robocop."

The AI assistant will use the MCP tools to perform these operations directly.
