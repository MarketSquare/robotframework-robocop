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
- "Configure Robocop to allow longer lines and disable naming checks"

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

#### Disabling Caching

The MCP server caches responses for discovery and documentation tools (like `list_rules`, `get_rule_info`) to reduce token usage. If you're developing custom rules and want fresh results on every request, disable caching with:

```bash
ROBOCOP_MCP_NO_CACHE=1 robocop-mcp
```

For Claude Desktop or other MCP clients, add the environment variable to the configuration:

```json
{
  "mcpServers": {
    "robocop": {
      "command": "robocop-mcp",
      "env": {
        "ROBOCOP_MCP_NO_CACHE": "1"
      }
    }
  }
}
```

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
| `offset` | int | Number of issues to skip for pagination (default: 0) |
| `configure` | list[str] | Rule configurations |
| `group_by` | string | Group results: `"severity"`, `"rule"`, or `"file"` |
| `summarize_only` | bool | Return only stats without individual issues (default: false) |

**Returns:** Dictionary with `total_files`, `total_issues`, `files_with_issues`, `issues` (omitted when `summarize_only`), `summary`, `limited`, `offset`, `has_more`, `unmatched_patterns`, `group_counts` (when grouped), and `top_rules` (when `summarize_only`).

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

Format Robot Framework code and lint the result in one operation. **Recommended for cleaning up code** — it formats first, then shows remaining issues that need manual fixes. Can process either inline content or a file from disk.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code (use this OR `file_path`) |
| `file_path` | string | Absolute path to .robot or .resource file (use this OR `content`) |
| `filename` | string | Virtual filename when using content (default: "stdin.robot") |
| `lint_select` | list[str] | Linter rule IDs/names to enable |
| `lint_ignore` | list[str] | Linter rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `format_select` | list[str] | Formatter names to apply |
| `space_count` | int | Spaces for indentation (default: 4) |
| `line_length` | int | Maximum line length (default: 120) |
| `limit` | int | Maximum issues to return |
| `configure` | list[str] | Rule configurations |
| `overwrite` | bool | If True and `file_path` is used, write formatted content back to file (default: false) |

**Returns:** Dictionary with `formatted`, `changed`, `diff`, `issues` (remaining), `issues_before`, `issues_after`, `issues_fixed`. When `file_path` is used, also includes `file` and `written`.

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
| `summarize_only` | bool | Return only stats without per-file results (default: false) |

**Returns:** Dictionary with `total_files`, `files_changed`, `files_unchanged`, `files_written`, `results` (omitted when `summarize_only`), `errors`, `unmatched_patterns`.

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

##### worst_files

Find the N files with the most linting issues. Useful for prioritizing cleanup efforts in large codebases.

| Parameter | Type | Description |
|-----------|------|-------------|
| `directory_path` | string | Absolute path to directory (required) |
| `n` | int | Number of files to return (default: 10) |
| `recursive` | bool | Search subdirectories (default: true) |
| `select` | list[str] | Rule IDs/names to enable |
| `ignore` | list[str] | Rule IDs/names to ignore |
| `threshold` | string | Minimum severity: `I`, `W`, or `E` |
| `configure` | list[str] | Rule configurations |

**Returns:** Dictionary with:

- `files`: List of worst files, each with `file`, `issue_count`, `severity_breakdown`
- `total_files_analyzed`: Total files scanned
- `files_with_issues`: Files that have at least one issue

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

#### LLM-Assisted Fixing Tools

These tools enable AI assistants to generate and apply intelligent fixes for Robot Framework code issues.

##### get_fix_context

Get rich context for LLM-assisted fixing of Robot Framework code issues. This tool provides everything an AI needs to generate a proper fix: the problematic code snippet, detailed issue information, rule documentation, and structured guidance.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Robot Framework source code (use this OR `file_path`) |
| `file_path` | string | Absolute path to .robot or .resource file (use this OR `content`) |
| `filename` | string | Virtual filename when using content (default: "stdin.robot") |
| `line` | int | Specific line to get context for (None = all issues) |
| `rule_ids` | list[str] | Filter to specific rule IDs (e.g., `["LEN01", "NAME02"]`) |
| `context_lines` | int | Lines of context before and after target (default: 5) |

**Returns:** Dictionary with:

- `file_path`: File path if from file
- `full_content`: The complete file/content being analyzed
- `target_snippet`: The problematic code section with `content`, `start_line`, `end_line`
- `issues`: List of issues with `rule_id`, `name`, `message`, `severity`, `line`, `column`, `fix_suggestion`, `rule_docs`
- `llm_guidance`: Structured guidance for the LLM on how to generate the fix

##### apply_fix

Apply an LLM-generated fix to Robot Framework code. Takes a line-based replacement and applies it to the code, then validates the fix by re-linting to ensure issues were actually resolved.

| Parameter | Type | Description |
|-----------|------|-------------|
| `content` | string | Original Robot Framework source (use this OR `file_path`) |
| `file_path` | string | Path to the file to fix (use this OR `content`) |
| `filename` | string | Virtual filename when using content (default: "stdin.robot") |
| `replacement` | object | The line-based replacement with `start_line`, `end_line`, `new_content` (required) |
| `overwrite` | bool | Write the fix to disk - only with `file_path` (default: false) |
| `validate` | bool | Re-lint to validate the fix resolved issues (default: true) |
| `select` | list[str] | Rule IDs to check in validation |
| `ignore` | list[str] | Rule IDs to ignore in validation |

**Returns:** Dictionary with:

- `success`: Whether the fix was successfully applied and validated
- `file_path`: File path if written to disk
- `written`: Whether the fix was written to disk
- `new_content`: The content after applying the fix
- `diff`: Unified diff showing the changes
- `issues_before`: Number of issues before the fix
- `issues_after`: Number of issues after the fix
- `issues_fixed`: Number of issues resolved by the fix
- `remaining_issues`: Issues that remain after the fix (limited to first 10)
- `validation_error`: Error message if fix validation failed

**Example workflow:**

```python
# 1. Get context for an issue at line 42
context = get_fix_context(file_path="/path/to/test.robot", line=42)

# 2. AI uses context.llm_guidance and context.issues to generate a fix

# 3. Apply the fix
apply_fix(
    file_path="/path/to/test.robot",
    replacement={"start_line": 42, "end_line": 43, "new_content": "    Log    Fixed code"},
    overwrite=True
)
```

#### Natural Language Configuration Tools

These tools enable AI assistants to configure Robocop through natural language. Users can describe what they want (e.g., "allow longer lines" or "disable naming checks") and the AI generates the appropriate configuration.

The workflow is designed for **safe preview by default**:

1. `get_config_context` - Get rule catalog and instructions for LLM processing
2. `parse_config_response` - Parse LLM response into validated configuration (preview only)
3. `apply_configuration` - Write configuration to file (explicit action required)

##### get_config_context

Get the system message and instructions for natural language configuration. This provides all available rules, their parameters, and instructions for generating configuration suggestions.

**Parameters:** None

**Returns:** Dictionary with:

- `system_message`: Complete context including all rules organized by category, configurable parameters, and JSON response format instructions

##### parse_config_response

Parse an LLM's JSON response into validated configuration suggestions. This tool validates rule names, parameters, and values, returning ready-to-use TOML configuration.

!!! note "Preview Only"
    This tool has `readOnlyHint: True` - it does NOT write any files. The `toml_config` field contains the configuration for preview or manual use.

| Parameter | Type | Description |
|-----------|------|-------------|
| `llm_response` | string | The JSON response from the LLM after processing a natural language configuration request (required) |

**Expected LLM Response Format:**

```json
{
  "interpretation": "Brief summary of what you understood",
  "suggestions": [
    {
      "rule_id": "LEN02",
      "rule_name": "line-too-long",
      "action": "configure",
      "parameter": "line_length",
      "value": "140",
      "section": "lint",
      "interpretation": "Allow lines up to 140 characters",
      "explanation": "The line-too-long rule defaults to 120 chars"
    }
  ],
  "warnings": ["any ambiguities or issues"]
}
```

**Returns:** Dictionary with:

- `success`: Whether parsing was successful
- `suggestions`: List of validated configuration suggestions, each with:
  - `rule_id`: Rule identifier (e.g., "LEN02")
  - `rule_name`: Rule name (e.g., "line-too-long")
  - `action`: One of "configure", "enable", "disable", or "set"
  - `parameter`: Parameter name (for configure/set actions)
  - `value`: Value to set
  - `section`: Config section ("common", "lint", or "format")
  - `interpretation`: What we understood the user meant
  - `explanation`: Why this configuration is appropriate
- `toml_config`: Ready-to-use TOML configuration string
- `warnings`: Any ambiguities, conflicts, or issues found
- `explanation`: Summary of what the configuration achieves

##### apply_configuration

Apply Robocop configuration to a TOML file. This tool merges the new configuration with any existing settings.

!!! warning "File Modification"
    This tool writes to disk. Review the configuration using `parse_config_response` before applying.

| Parameter | Type | Description |
|-----------|------|-------------|
| `toml_config` | string | TOML configuration string to apply (required) |
| `file_path` | string | Path to configuration file (default: "pyproject.toml") |

**Supported file formats:**

- `pyproject.toml` / `robot.toml`: Uses `[tool.robocop.*]` sections
- `robocop.toml`: Uses root-level sections (`[lint]`, `[format]`)

**Returns:** Dictionary with:

- `success`: Whether the configuration was successfully applied
- `file_path`: Absolute path to the configuration file
- `file_created`: True if a new file was created
- `diff`: Unified diff showing changes made
- `merged_config`: The full configuration after merging
- `validation_passed`: True if configuration is valid
- `validation_error`: Error message if validation failed

**Example workflow:**

```python
# 1. Get context for LLM processing
context = get_config_context()
# context.system_message contains all rules and instructions

# 2. User asks: "Allow lines up to 140 characters and disable the too-many-calls-in-test rule"
# AI processes the request using the system message and generates JSON

# 3. Parse the AI's response (preview only - no file changes)
result = parse_config_response(llm_response='{"interpretation": "...", "suggestions": [...]}')
# result.toml_config contains:
# [tool.robocop.lint]
# configure = ["line-too-long.line_length=140"]
# ignore = ["too-many-calls-in-test"]

# 4. User reviews and approves, then apply to file
apply_configuration(
    toml_config=result.toml_config,
    file_path="pyproject.toml"
)
```

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

##### search_rules

Search for linting rules by keyword. Searches across rule names, messages, and documentation.

| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query - case-insensitive substring match (required) |
| `fields` | list[str] | Fields to search: `"name"`, `"message"`, `"docs"`, `"rule_id"` (default: all except rule_id) |
| `category` | string | Filter by category: `"LEN"`, `"NAME"`, `"DOC"`, etc. |
| `severity` | string | Filter by severity: `"I"`, `"W"`, or `"E"` |
| `limit` | int | Maximum results to return (default: 20) |

**Returns:** List of matching rules with `rule_id`, `name`, `message`, `severity`, `enabled`, `match_field`, `match_snippet`.

##### list_prompts

List all available MCP prompt templates. Use this to discover available prompts and their arguments.

**Returns:** List of prompt summaries with `name`, `description`, `arguments`.

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

#### LLM-Assisted Fixing

**Get context and apply AI-generated fixes:**
> "Get the context for the issue at line 42 in my test file so you can fix it"
>
> "Fix the naming issue at line 15 - get the context first, then generate and apply the fix"
>
> "Help me fix all the issues in this file one by one"

#### Natural Language Configuration

**Configure rules using natural language:**
> "Allow lines up to 140 characters and set indentation to 2 spaces"
>
> "Disable the naming rules for test cases"
>
> "I want to ignore the too-many-calls-in-test rule"

**Preview before applying:**
> "Show me what configuration would allow longer keywords"
>
> "Generate config to disable documentation checks, but don't save it yet"

**Apply to specific file:**
> "Configure Robocop to use 4-space indentation and save to pyproject.toml"
>
> "Add these rules to my robocop.toml file"

#### Configuring Rules

**Custom thresholds:**
> "Lint this code but allow lines up to 140 characters"
>
> "Check this file with max keyword length set to 50"

The AI assistant uses the MCP tools to perform these operations and returns the results in a readable format.

## Alternative: robocop-mcp

There is also a separate MCP server implementation available at [robocop-mcp](https://github.com/aaltat/robocop-mcp). This is an independent project that provides similar functionality.
