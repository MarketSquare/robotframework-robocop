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
