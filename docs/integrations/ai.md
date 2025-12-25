# AI Integration

Robocop can be used directly in the Python code [Python API Reference](../user_guide/python_api.md), and it is possible to automate workflows using AI.

## MCP Server

Robocop provides a built-in MCP (Model Context Protocol) server that allows AI assistants to lint and format Robot Framework code directly. With MCP, you can ask your AI assistant to check your Robot Framework code for issues, format it, or explain specific rules—all through natural conversation.

### What Can You Do With It?

Once configured, you can ask your AI assistant things like:

- "Check this Robot Framework code for issues"
- "Lint all the robot files in my tests folder"
- "Format this test and show me what issues remain"
- "What does the LEN01 rule check for?"
- "Show me all naming-related rules"

### Installation

Install Robocop with MCP support:

```bash
pip install robotframework-robocop[mcp]
```

!!! note "Python Version Requirement"
    MCP support requires Python 3.10 or higher. The core Robocop functionality still supports Python 3.9+.

### Running the Server

#### Standalone (Testing)

To verify the installation works, run:

```bash
robocop-mcp
```

The server communicates over stdio, so you won't see any output—this is expected. Press `Ctrl+C` to stop.

#### With Claude Desktop

Add to your Claude Desktop configuration:

| OS | Config File Location |
|----|---------------------|
| Linux | `~/.config/claude-desktop/config.json` |
| macOS | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |

```json
{
  "mcpServers": {
    "robocop": {
      "command": "robocop-mcp"
    }
  }
}
```

After saving, restart Claude Desktop. You should see "robocop" listed in the MCP servers (click the hammer icon).

#### With uvx (Recommended)

Using uvx ensures you always have the latest version without manual updates:

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

!!! tip "uvx Installation"
    Install uvx via `pip install uvx` or see [uv documentation](https://docs.astral.sh/uv/).

#### With Claude Code (VS Code Extension)

Add to your VS Code settings (`.vscode/settings.json` or user settings):

```json
{
  "claudeCode.mcpServers": {
    "robocop": {
      "command": "robocop-mcp"
    }
  }
}
```

Or with uvx:

```json
{
  "claudeCode.mcpServers": {
    "robocop": {
      "command": "uvx",
      "args": ["--from", "robotframework-robocop[mcp]", "robocop-mcp"]
    }
  }
}
```

#### Troubleshooting

If the server doesn't appear or tools don't work:

1. **Verify installation**: Run `robocop-mcp` in terminal—it should start without errors
2. **Check Python version**: MCP requires Python 3.10+
3. **Restart the application**: Claude Desktop/VS Code needs restart after config changes
4. **Check config syntax**: Ensure valid JSON (no trailing commas)
5. **Path issues**: If `robocop-mcp` isn't found, use the full path (e.g., `/usr/local/bin/robocop-mcp`)

### Available Tools

#### Linting Tools

##### lint_content

Lint Robot Framework code provided as text content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code to lint (required) |
| `filename` | string | Virtual filename for file type detection (default: "stdin.robot") |
| `select` | list[str] | Rule IDs/names to enable (e.g., `["LEN01", "too-long-keyword"]`) |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I` (Info), `W` (Warning), or `E` (Error) |
| `limit` | int | Maximum number of issues to return |
| `configure` | list[str] | Rule configurations (e.g., `["line-too-long.line_length=140"]`) |

**Returns:** List of diagnostic issues, each containing `rule_id`, `name`, `message`, `severity`, `line`, `column`, `end_line`, `end_column`.

##### lint_file

Lint a single Robot Framework file from disk.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Absolute path to .robot or .resource file (required) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `limit` | int | Maximum number of issues to return |
| `configure` | list[str] | Rule configurations |

**Returns:** List of diagnostic issues (same format as lint_content).

##### lint_files

Lint multiple Robot Framework files using paths or glob patterns. Useful for checking specific files or patterns without scanning an entire directory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_patterns` | list[str] | File paths or glob patterns (required). Examples: `["test.robot"]`, `["tests/**/*.robot"]`, `["*.resource"]` |
| `base_path` | string | Base directory for relative paths/patterns (default: current directory) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `limit` | int | Maximum issues to return (per group if `group_by` is set) |
| `configure` | list[str] | Rule configurations |
| `group_by` | string | Group results: `"severity"`, `"rule"`, or `"file"` |

**Returns:** Dictionary with `total_files`, `total_issues`, `files_with_issues`, `issues`, `summary`, `limited`, `unmatched_patterns`, and `group_counts` (when grouped).

##### lint_directory

Lint all Robot Framework files in a directory.

| Parameter | Type | Description |
|-----------|------|-------------|
| `directory_path` | string | Absolute path to directory (required) |
| `recursive` | bool | Search subdirectories (default: true) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `limit` | int | Maximum issues to return (per group if `group_by` is set) |
| `configure` | list[str] | Rule configurations |
| `group_by` | string | Group results: `"severity"`, `"rule"`, or `"file"` |

**Returns:** Dictionary with `total_files`, `total_issues`, `files_with_issues`, `issues`, `summary`, `limited`, and `group_counts` (when grouped).

##### suggest_fixes

Analyze Robot Framework code and get actionable fix suggestions for each issue.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code to analyze (required) |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `rule_ids` | list[str] | Specific rule IDs to get suggestions for |

**Returns:** Dictionary with:

- `fixes`: List of suggestions, each with `rule_id`, `name`, `line`, `message`, `suggestion`, `auto_fixable`
- `total_issues`: Total issues found
- `auto_fixable`: Count of issues fixable by formatting
- `manual_required`: Count of issues needing manual fixes
- `recommendation`: Overall fix recommendation

#### Formatting Tools

##### format_content

Format Robot Framework code and return the formatted result.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code to format (required) |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `select` | list[str] | Formatter names to apply (default: all enabled formatters) |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |

**Returns:** Dictionary with `formatted` (the code), `changed` (boolean), and `diff` (unified diff if changed).

##### lint_and_format

Format Robot Framework code and lint the result in one operation. **Recommended for cleaning up code** — it formats first, then shows remaining issues that need manual fixes.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code (required) |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `lint_select` | list[str] | Linter rule IDs/names to enable |
| `lint_ignore` | list[str] | Linter rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `format_select` | list[str] | Formatter names to apply |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |
| `limit` | int | Maximum issues to return |
| `configure` | list[str] | Rule configurations |

**Returns:** Dictionary with `formatted`, `changed`, `diff`, `issues` (remaining), `issues_before`, `issues_after`, and `issues_fixed`.

##### format_file

Format a Robot Framework file from disk. Can optionally overwrite the file with formatted content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_path` | string | Absolute path to .robot or .resource file (required) |
| `select` | list[str] | Formatter names to apply (default: all enabled formatters) |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |
| `overwrite` | bool | Write formatted content back to file (default: false) |

**Returns:** Dictionary with `file`, `formatted`, `changed`, `diff`, and `written` (whether file was overwritten).

##### format_files

Format multiple Robot Framework files using paths or glob patterns. Can optionally overwrite files with formatted content.

| Parameter | Type | Description |
|-----------|------|-------------|
| `file_patterns` | list[str] | File paths or glob patterns (required). Examples: `["test.robot"]`, `["tests/**/*.robot"]` |
| `base_path` | string | Base directory for relative paths/patterns (default: current directory) |
| `select` | list[str] | Formatter names to apply |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |
| `overwrite` | bool | Write formatted content back to files (default: false) |

**Returns:** Dictionary with `total_files`, `files_changed`, `files_unchanged`, `files_written`, `results`, `errors`, `unmatched_patterns`.

#### Statistics Tools

##### get_statistics

Get code quality statistics for a Robot Framework codebase. Provides a high-level overview including quality score, most common issues, and recommendations.

| Parameter | Type | Description |
|-----------|------|-------------|
| `directory_path` | string | Absolute path to directory (required) |
| `recursive` | bool | Search subdirectories (default: true) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `configure` | list[str] | Rule configurations |

**Returns:** Dictionary with:

- `directory`: The analyzed path
- `summary`: Stats including `total_files`, `files_with_issues`, `files_clean`, `total_issues`, `avg_issues_per_file`, `max_issues_in_file`
- `severity_breakdown`: Issues by severity `{E: count, W: count, I: count}`
- `top_issues`: List of most common rules with counts
- `quality_score`: Contains `score` (0-100), `grade` (A-F), and `label`
- `recommendations`: List of actionable suggestions

#### Explanation Tools

##### explain_issue

Explain a specific issue at a given line with surrounding context. More detailed than `get_rule_info` because it shows the actual code context.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code to analyze (required) |
| `line` | int | The line number to explain (1-indexed, required) |
| `filename` | string | Virtual filename (default: "stdin.robot") |
| `context_lines` | int | Number of lines to show before/after (default: 3) |

**Returns:** Dictionary with:

- `line`: The requested line number
- `issues_found`: Boolean indicating if issues were found
- `issues`: List of detailed explanations with `rule_id`, `name`, `message`, `severity`, `why_it_matters`, `fix_suggestion`, `full_documentation`, `configurable_parameters`
- `related_issues`: Issues on nearby lines (within 2 lines)
- `context`: Surrounding code with line numbers

#### Discovery Tools

##### list_rules

List all available linting rules with optional filtering.

| Parameter | Type | Description |
|-----------|------|-------------|
| `category` | string | Filter by category: `"LEN"`, `"NAME"`, `"DOC"`, `"SPACE"`, etc. |
| `severity` | string | Filter by severity: `"I"`, `"W"`, or `"E"` |
| `enabled_only` | bool | Only return enabled rules (default: false) |

**Returns:** List of rule summaries with `rule_id`, `name`, `severity`, `enabled`, `message`.

##### list_formatters

List all available formatters.

| Parameter | Type | Description |
|-----------|------|-------------|
| `enabled_only` | bool | Only return enabled formatters (default: true) |

**Returns:** List of formatter summaries with `name`, `enabled`, `description`.

##### get_rule_info

Get detailed documentation for a specific linting rule.

| Parameter | Type | Description |
|-----------|------|-------------|
| `rule_name_or_id` | string | Rule name (e.g., `"too-long-keyword"`) or ID (e.g., `"LEN01"`) (required) |

**Returns:** Dictionary with `rule_id`, `name`, `message`, `severity`, `enabled`, `deprecated`, `docs`, `parameters`, `added_in_version`, `version_requirement`.

##### get_formatter_info

Get detailed documentation for a specific formatter.

| Parameter | Type | Description |
|-----------|------|-------------|
| `formatter_name` | string | Formatter name (e.g., `"NormalizeSeparators"`) (required) |

**Returns:** Dictionary with `name`, `enabled`, `docs`, `min_version`, `parameters`, `skip_options`.

### Available Resources

Resources provide read-only context data.

#### robocop://rules

Complete catalog of all available linting rules with basic information.

#### robocop://formatters

Complete catalog of all available formatters.

#### robocop://rules/{rule_id}

Detailed information about a specific rule, including full documentation and parameters.

### Available Prompts

Prompts provide reusable templates for common operations. These guide the AI assistant through multi-step workflows.

#### analyze_robot_file

Template for comprehensive Robot Framework code analysis.

| Argument | Description |
|----------|-------------|
| `content` | The Robot Framework code to analyze |
| `focus` | Analysis focus: `"all"`, `"style"`, `"errors"`, or `"best-practices"` |

#### fix_robot_issues

Template for fixing all issues in Robot Framework code.

| Argument | Description |
|----------|-------------|
| `content` | The Robot Framework code to fix |

#### explain_rule

Template for explaining a Robocop rule with examples.

| Argument | Description |
|----------|-------------|
| `rule_name_or_id` | The rule to explain |
| `code_snippet` | Optional code that triggered the rule |

#### review_pull_request

Template for reviewing Robot Framework files in a pull request.

| Argument | Description |
|----------|-------------|
| `file_paths` | Comma-separated list of file paths to review |

#### configure_robocop

Template for configuring Robocop for a specific project type.

| Argument | Description |
|----------|-------------|
| `project_type` | Type of project: `"generic"`, `"api-testing"`, `"ui-testing"`, or `"data-driven"` |

#### migrate_to_latest

Template for identifying deprecated patterns when upgrading Robot Framework versions.

| Argument | Description |
|----------|-------------|
| `current_rf_version` | Current Robot Framework version (e.g., `"4.x"`, `"5.x"`, `"6.x"`) |

### Example Usage

Once the MCP server is configured, you can use natural language to interact with Robocop through your AI assistant. Here are practical examples:

#### Basic Linting

**Check inline code:**
> "Check this Robot Framework code for issues:
> ```robot
> *** Test Cases ***
> test without capital
>     log  hello
> ```"

**Lint a file:**
> "Lint the file `/path/to/my_tests.robot`"

**Lint with filters:**
> "Check my tests but only show errors, ignore warnings"
>
> "Lint this code but only check for naming issues"

#### Batch Linting

**Lint multiple files:**
> "Lint all robot files in my tests folder"
>
> "Check `tests/**/*.robot` and `keywords/**/*.resource` for issues"

**Organize large results:**
> "Lint my test suite and group the issues by severity so I can fix errors first"
>
> "Check all robot files and group by rule so I can batch fix similar issues"

**Limit output:**
> "Lint the tests directory but only show me 10 issues per file"

#### Formatting

**Format code:**
> "Format this Robot Framework code"

**Format and see remaining issues:**
> "Clean up this code - format it and show me what issues still need manual fixes"

**Format files on disk:**
> "Format all robot files in my tests folder"
>
> "Format `tests/**/*.robot` and save the changes"

#### Codebase Statistics

**Get quality overview:**
> "Give me an overview of code quality in my test suite"
>
> "What's the quality score for my tests directory?"

**Identify problem areas:**
> "What are the most common issues in my codebase?"
>
> "Show me statistics for my robot files"

#### Explaining Issues

**Understand specific issues:**
> "Why is line 42 flagged? Explain with context"
>
> "Explain the issue at line 15 in this code"

#### Understanding Rules

**Get rule details:**
> "What does the LEN01 rule check for?"
>
> "Explain the too-long-keyword rule and how to configure it"

**Discover rules:**
> "Show me all naming-related rules"
>
> "What error-level rules does Robocop have?"
>
> "List all documentation rules"

#### Getting Fix Suggestions

**Get actionable fixes:**
> "Analyze this code and tell me how to fix each issue"
>
> "What issues in this code can be auto-fixed vs need manual changes?"

#### Configuring Rules

**Custom thresholds:**
> "Lint this code but allow lines up to 140 characters"
>
> "Check this file with max keyword length set to 50"

The AI assistant uses the MCP tools to perform these operations and returns the results in a readable format.

## Alternative: robocop-mcp

There is also a separate MCP server implementation available at [robocop-mcp](https://github.com/aaltat/robocop-mcp). This is an independent project that provides similar functionality.
