"""MCP Prompts for Robocop - Reusable prompt templates for common operations."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register all MCP prompts with the server."""

    @mcp.prompt()
    def analyze_robot_file(content: str, focus: str = "all") -> str:
        """
        Generate a prompt for analyzing Robot Framework code.

        Args:
            content: The Robot Framework code to analyze
            focus: Analysis focus - "all", "style", "errors", or "best-practices"

        Returns:
                str: The prompt for analyzing the Robot Framework code.

        """
        focus_instructions = {
            "all": "Check for all types of issues including errors, warnings, and style suggestions.",
            "style": "Focus on code style, naming conventions, and formatting.",
            "errors": "Focus on critical errors that may cause test failures.",
            "best-practices": "Focus on Robot Framework best practices and maintainability.",
        }

        instruction = focus_instructions.get(focus, focus_instructions["all"])

        return f"""Analyze the following Robot Framework code for issues.

**Focus**: {instruction}

**Instructions**:
1. Use the `lint_content` tool to get a list of diagnostics
2. Summarize the issues found, grouped by severity (Errors, Warnings, Info)
3. Explain the most critical problems and their impact
4. Suggest specific fixes for each issue
5. Identify any patterns that indicate larger architectural problems

**Code to analyze**:
```robot
{content}
```
"""

    @mcp.prompt()
    def fix_robot_issues(content: str) -> str:
        """
        Generate a prompt for fixing issues in Robot Framework code.

        Args:
            content: The Robot Framework code to fix

        Returns:
            str: The prompt for fixing issues in the Robot Framework code.

        """
        return f"""Fix all issues in the following Robot Framework code.

**Instructions**:
1. First, use `lint_content` to identify all issues in the code
2. Then, use `format_content` to apply automatic formatting fixes
3. Review the remaining issues that require manual fixes
4. Apply manual fixes to address any remaining problems
5. Provide the corrected code with explanations of what was changed

**Important**:
- Preserve the original test logic and intent
- Fix formatting, naming, and style issues
- Address any errors or warnings
- Do not change the test behavior unless it's clearly broken

**Code to fix**:
```robot
{content}
```
"""

    @mcp.prompt()
    def explain_rule(rule_name_or_id: str, code_snippet: str = "") -> str:
        """
        Generate a prompt for explaining a Robocop rule.

        Args:
            rule_name_or_id: The rule ID or name to explain
            code_snippet: Optional code that triggered the rule

        Returns:
            str: The prompt for explaining the Robocop rule.

        """
        code_section = ""
        if code_snippet:
            code_section = f"""
**Code that triggered this rule**:
```robot
{code_snippet}
```

Explain why this code triggers the rule and how to fix it.
"""

        return f"""Explain the Robocop rule "{rule_name_or_id}" in detail.

**Instructions**:
1. Use `get_rule_info` to get the full documentation for this rule
2. Explain what the rule checks for and why it matters
3. Provide examples of code that violates this rule
4. Show how to fix violations
5. Explain any configurable parameters and when to adjust them
{code_section}
"""

    @mcp.prompt()
    def review_pull_request(file_paths: str) -> str:
        """
        Generate a prompt for reviewing Robot Framework files in a pull request.

        Args:
            file_paths: Comma-separated list of file paths to review

        Returns:
            str: The prompt for reviewing the pull request.

        """
        paths = [p.strip() for p in file_paths.split(",")]
        paths_list = "\n".join(f"- {p}" for p in paths)

        return f"""Review the following Robot Framework files for a pull request.

**Files to review**:
{paths_list}

**Instructions**:
1. For each file, use `lint_file` to get linting issues
2. Categorize issues by severity (Errors, Warnings, Info)
3. Identify patterns across files that indicate systemic problems
4. Check for:
   - Consistent naming conventions
   - Proper documentation
   - Code style and formatting
   - Test structure and organization
   - Potential maintenance issues
5. Provide a summary with:
   - Overall code quality assessment
   - Must-fix issues (errors and critical warnings)
   - Suggested improvements (optional fixes)
   - Positive observations (good practices found)

**Output format**:
Provide a structured review suitable for a pull request comment.
"""

    @mcp.prompt()
    def configure_robocop(project_type: str = "generic") -> str:
        """
        Generate a prompt for configuring Robocop for a project.

        Args:
            project_type: Type of project - "generic", "api-testing", "ui-testing", "data-driven"

        Returns:
            str: The prompt for configuring Robocop.

        """
        project_hints = {
            "generic": "a general-purpose Robot Framework project",
            "api-testing": "an API testing project (likely uses RequestsLibrary, REST APIs)",
            "ui-testing": "a UI/browser testing project (likely uses SeleniumLibrary or Browser)",
            "data-driven": "a data-driven testing project (heavy use of templates and variables)",
        }

        project_desc = project_hints.get(project_type, project_hints["generic"])

        return f"""Help configure Robocop for {project_desc}.

**Instructions**:
1. Use `list_rules` to see all available rules
2. Use `list_formatters` to see all available formatters
3. Based on the project type, recommend:
   - Which rules to enable/disable
   - Rule configuration adjustments (using `configure` parameter)
   - Which formatters to use
   - Appropriate thresholds for CI/CD integration

**Provide**:
1. A sample `.robocop` configuration file with recommended settings
2. Explanation of why each setting is recommended for this project type
3. CI/CD integration suggestions (pre-commit hooks, GitHub Actions, etc.)
4. Common rule customizations for this project type

**Project type context**: {project_type}
- Consider typical patterns and needs for this type of project
- Suggest rules that catch common mistakes in this domain
- Recommend formatters that enforce appropriate style
"""

    @mcp.prompt()
    def migrate_to_latest(current_rf_version: str = "4.x") -> str:
        """
        Generate a prompt for identifying deprecated patterns during Robot Framework upgrade.

        Args:
            current_rf_version: Current Robot Framework version (e.g., "4.x", "5.x", "6.x")

        Returns:
            str: The prompt for identifying deprecated patterns.

        """
        return f"""Help identify deprecated patterns for upgrading from Robot Framework {current_rf_version}.

**Instructions**:
1. Use `list_rules` to find rules related to deprecation
2. Use `lint_directory` or `lint_file` on the project files
3. Focus on rules that detect:
   - Deprecated syntax
   - Removed features
   - Changed behavior
   - Best practices for newer versions

**Provide**:
1. List of deprecated patterns found in the codebase
2. For each pattern:
   - What it is and why it's deprecated
   - The recommended replacement
   - Code examples showing before/after
3. Priority order for fixes (breaking changes first)
4. Estimated effort for migration
5. Testing recommendations after migration

**Current version**: Robot Framework {current_rf_version}
**Target version**: Latest Robot Framework (7.x)

Note: Some rules may need version-specific configuration. Use the `configure` parameter
to adjust version checks as needed.
"""
