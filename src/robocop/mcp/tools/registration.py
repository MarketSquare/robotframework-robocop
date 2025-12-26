"""MCP tool registration - FastMCP server tool registration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context

from robocop.mcp.tools.batch_operations import (
    _collect_robot_files,
    _format_files_impl,
    _group_issues,
    _lint_files_impl,
)
from robocop.mcp.tools.diagnostics import (
    _explain_issue_impl,
    _get_statistics_impl,
    _suggest_fixes_impl,
)
from robocop.mcp.tools.documentation import (
    _get_formatter_info_impl,
    _get_rule_info_impl,
    _list_formatters_impl,
    _list_rules_impl,
)
from robocop.mcp.tools.formatting import _format_content_impl, _format_file_impl
from robocop.mcp.tools.linting import _lint_content_impl, _lint_file_impl

if TYPE_CHECKING:
    from fastmcp import FastMCP


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Robot Framework Content"},
    )
    async def lint_content(
        content: str,
        filename: str = "stdin.robot",
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
        configure: list[str] | None = None,
        ctx: Context | None = None,
    ) -> list[dict]:
        """
        Lint Robot Framework code provided as text content.

        Args:
            content: Robot Framework source code to lint
            filename: Virtual filename (affects file type detection, use .robot or .resource)
            select: List of rule IDs/names to enable (e.g., ["LEN01", "too-long-keyword"])
            ignore: List of rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            limit: Maximum number of issues to return (None = no limit)
            configure: List of rule configurations (e.g., ["line-too-long.line_length=140"])

        Returns:
            List of diagnostic issues found, each containing:
            - rule_id: The rule identifier (e.g., "LEN01")
            - name: The rule name (e.g., "too-long-keyword")
            - message: Description of the issue
            - severity: I/W/E
            - line: Line number (1-indexed)
            - column: Column number (1-indexed)
            - end_line: End line number
            - end_column: End column number

        Example::

            lint_content("*** Test Cases ***...")
            # Returns: [{"rule_id": "NAME02", "name": "wrong-case-in-test-case-name", ...}]

        """
        if ctx:
            await ctx.info(f"Linting content ({len(content)} bytes)...")

        result = _lint_content_impl(content, filename, select, ignore, threshold, limit, configure)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Robot Framework File"},
    )
    async def lint_file(
        file_path: str,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
        configure: list[str] | None = None,
        ctx: Context | None = None,
    ) -> list[dict]:
        """
        Lint a Robot Framework file from disk.

        Args:
            file_path: Absolute path to the .robot or .resource file
            select: List of rule IDs/names to enable
            ignore: List of rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            limit: Maximum number of issues to return (None = no limit)
            configure: List of rule configurations (e.g., ["line-too-long.line_length=140"])

        Returns:
            List of diagnostic issues found (same format as lint_content)

        Example::

            lint_file("/path/to/test.robot")
            lint_file("/path/to/test.robot", select=["LEN*"], threshold="W")

        """
        if ctx:
            await ctx.info(f"Linting file: {file_path}")

        result = _lint_file_impl(file_path, select, ignore, threshold, limit=limit, configure=configure)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Directory"},
    )
    async def lint_directory(
        directory_path: str,
        recursive: bool = True,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
        configure: list[str] | None = None,
        group_by: str | None = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Lint all Robot Framework files in a directory.

        Args:
            directory_path: Absolute path to the directory containing .robot/.resource files
            recursive: Whether to search subdirectories (default: True)
            select: List of rule IDs/names to enable
            ignore: List of rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            limit: Maximum number of issues to return. When group_by is set,
                this limit applies per group instead of globally.
            configure: List of rule configurations (e.g., ["line-too-long.line_length=140"])
            group_by: Group results by "severity", "rule", or "file". When set:
                - "severity": Group by E/W/I for prioritized fixing
                - "rule": Group by rule ID for batch fixing same issues
                - "file": Group by file path for file-by-file review

        Returns:
            Dictionary containing:
            - total_files: Number of files linted
            - total_issues: Total number of issues found
            - files_with_issues: Number of files that have issues
            - issues: List of issues, or dict grouped by key when group_by is set
            - summary: Issues by severity {E: count, W: count, I: count}
            - limited: Boolean indicating if results were truncated
            - group_counts: (only when group_by set) Total count per group before limit

        Raises:
            ToolError: If the directory does not exist or contains no Robot Framework files

        Example::

            lint_directory("/path/to/tests")
            lint_directory("/path/to/tests", recursive=False, threshold="E")
            lint_directory("/path/to/tests", group_by="severity", limit=10)

        """
        path = Path(directory_path)

        if not path.exists():
            raise ToolError(f"Directory not found: {directory_path}")

        if not path.is_dir():
            raise ToolError(f"Not a directory: {directory_path}")

        files = _collect_robot_files(path, recursive)

        if not files:
            raise ToolError(f"No .robot or .resource files found in {directory_path}")

        if ctx:
            await ctx.info(f"Found {len(files)} Robot Framework file(s) to lint")

        all_issues: list[dict] = []
        files_with_issues = 0
        summary = {"E": 0, "W": 0, "I": 0}

        for i, file in enumerate(files):
            if ctx:
                await ctx.report_progress(progress=i, total=len(files))

            try:
                issues = _lint_file_impl(
                    str(file),
                    select,
                    ignore,
                    threshold,
                    include_file_in_result=True,
                    configure=configure,
                )
                if issues:
                    files_with_issues += 1
                    all_issues.extend(issues)
                    for issue in issues:
                        severity = issue.get("severity", "W")
                        if severity in summary:
                            summary[severity] += 1
            except ToolError:
                # Skip files that fail to parse
                if ctx:
                    await ctx.warning(f"Failed to parse: {file}")

        total_issues = len(all_issues)

        if ctx:
            await ctx.report_progress(progress=len(files), total=len(files))

        # Handle grouping vs flat list
        if group_by:
            grouped_issues, group_counts = _group_issues(all_issues, group_by, limit)
            limited = any(group_counts[k] > len(v) for k, v in grouped_issues.items())

            if ctx:
                msg = f"Completed: {total_issues} issue(s) in {files_with_issues} file(s)"
                if limited:
                    msg += f" (limited to {limit} per group)"
                await ctx.info(msg)

            return {
                "total_files": len(files),
                "total_issues": total_issues,
                "files_with_issues": files_with_issues,
                "issues": grouped_issues,
                "summary": summary,
                "limited": limited,
                "group_counts": group_counts,
            }

        # Flat list mode (original behavior)
        limited = limit is not None and total_issues > limit
        if limited:
            all_issues = all_issues[:limit]

        if ctx:
            msg = f"Completed: {total_issues} issue(s) in {files_with_issues} file(s)"
            if limited:
                msg += f" (showing first {limit})"
            await ctx.info(msg)

        return {
            "total_files": len(files),
            "total_issues": total_issues,
            "files_with_issues": files_with_issues,
            "issues": all_issues,
            "summary": summary,
            "limited": limited,
        }

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Lint Multiple Robot Files"},
    )
    async def lint_files(
        file_patterns: list[str],
        base_path: str | None = None,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
        configure: list[str] | None = None,
        group_by: str | None = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Lint multiple Robot Framework files specified by paths or glob patterns.

        This tool allows linting a specific set of files without linting an entire
        directory. Useful for checking only changed files or a specific subset.

        Args:
            file_patterns: List of file paths or glob patterns to lint. Examples:
                - Explicit paths: ["/path/to/test.robot", "tests/login.robot"]
                - Glob patterns: ["tests/**/*.robot", "*.resource"]
                - Mixed: ["specific.robot", "suite/**/*.robot"]
            base_path: Base directory for resolving relative paths and patterns.
                Defaults to current working directory.
            select: List of rule IDs/names to enable (e.g., ["LEN01", "too-long-keyword"])
            ignore: List of rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            limit: Maximum number of issues to return. When group_by is set,
                this limit applies per group instead of globally.
            configure: List of rule configurations (e.g., ["line-too-long.line_length=140"])
            group_by: Group results by "severity", "rule", or "file". When set:
                - "severity": Group by E/W/I for prioritized fixing
                - "rule": Group by rule ID for batch fixing same issues
                - "file": Group by file path for file-by-file review

        Returns:
            Dictionary containing:
            - total_files: Number of files linted
            - total_issues: Total number of issues found
            - files_with_issues: Number of files that have issues
            - issues: List of issues, or dict grouped by key when group_by is set
            - summary: Issues by severity {E: count, W: count, I: count}
            - limited: Boolean indicating if results were truncated
            - unmatched_patterns: List of patterns that didn't match any files
            - group_counts: (only when group_by set) Total count per group before limit

        Raises:
            ToolError: If no valid Robot Framework files are found

        Example::

            lint_files(["tests/login.robot", "tests/checkout.robot"])
            lint_files(["tests/**/*.robot"], threshold="W")
            lint_files(["*.robot"], group_by="severity", limit=10)

        """
        if ctx:
            await ctx.info(f"Processing {len(file_patterns)} file pattern(s)...")

        return _lint_files_impl(file_patterns, base_path, select, ignore, threshold, limit, configure, group_by)

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "title": "Format Robot Framework Code",
        },
    )
    async def format_content(
        content: str,
        filename: str = "stdin.robot",
        select: list[str] | None = None,
        space_count: int = 4,
        line_length: int = 120,
        ctx: Context | None = None,
    ) -> dict:
        """
        Format Robot Framework code and return the formatted result.

        Args:
            content: Robot Framework source code to format
            filename: Virtual filename (affects parsing)
            select: List of formatter names to apply (if empty, uses defaults)
            space_count: Number of spaces for indentation (default: 4)
            line_length: Maximum line length (default: 120)

        Returns:
            Dictionary containing:
            - formatted: The formatted source code
            - changed: Boolean indicating if content was modified
            - diff: Unified diff if content changed, None otherwise

        Example::

            format_content(robot_code)
            # Returns: {"formatted": "...", "changed": True, "diff": "..."}

        """
        if ctx:
            await ctx.info(f"Formatting content ({len(content)} bytes)...")

        result = _format_content_impl(content, filename, select, space_count, line_length)

        if ctx:
            status = "Content modified" if result["changed"] else "No changes needed"
            await ctx.info(status)

        return result

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "idempotentHint": True,
            "title": "Format Robot Framework File",
        },
    )
    async def format_file(
        file_path: str,
        select: list[str] | None = None,
        space_count: int = 4,
        line_length: int = 120,
        overwrite: bool = False,
        ctx: Context | None = None,
    ) -> dict:
        """
        Format a Robot Framework file from disk.

        This tool reads a file, formats it, and optionally writes the formatted
        content back to disk. Use overwrite=True to modify the file in place.

        Args:
            file_path: Absolute path to the .robot or .resource file
            select: List of formatter names to apply (if empty, uses defaults)
            space_count: Number of spaces for indentation (default: 4)
            line_length: Maximum line length (default: 120)
            overwrite: If True, write formatted content back to the file (default: False)

        Returns:
            Dictionary containing:
            - file: The file path
            - formatted: The formatted source code
            - changed: Boolean indicating if content was modified
            - diff: Unified diff if content changed, None otherwise
            - written: Boolean indicating if the file was overwritten

        Example::

            format_file("/path/to/test.robot")  # Preview changes
            format_file("/path/to/test.robot", overwrite=True)  # Apply changes

        """
        if ctx:
            mode = "formatting and overwriting" if overwrite else "formatting (preview)"
            await ctx.info(f"{mode.capitalize()}: {file_path}")

        result = _format_file_impl(file_path, select, space_count, line_length, overwrite=overwrite)

        if ctx:
            if result["changed"]:
                status = "File modified and saved" if result["written"] else "Changes detected (not saved)"
            else:
                status = "No changes needed"
            await ctx.info(status)

        return result

    @mcp.tool(
        tags={"formatting"},
        annotations={
            "idempotentHint": True,
            "title": "Format Multiple Robot Files",
        },
    )
    async def format_files(
        file_patterns: list[str],
        base_path: str | None = None,
        select: list[str] | None = None,
        space_count: int = 4,
        line_length: int = 120,
        overwrite: bool = False,
        ctx: Context | None = None,
    ) -> dict:
        """
        Format multiple Robot Framework files specified by paths or glob patterns.

        This tool allows formatting a specific set of files without formatting an
        entire directory. Use overwrite=True to modify files in place.

        Args:
            file_patterns: List of file paths or glob patterns to format. Examples:
                - Explicit paths: ["/path/to/test.robot", "tests/login.robot"]
                - Glob patterns: ["tests/**/*.robot", "*.resource"]
                - Mixed: ["specific.robot", "suite/**/*.robot"]
            base_path: Base directory for resolving relative paths and patterns.
                Defaults to current working directory.
            select: List of formatter names to apply (if empty, uses defaults)
            space_count: Number of spaces for indentation (default: 4)
            line_length: Maximum line length (default: 120)
            overwrite: If True, write formatted content back to files (default: False)

        Returns:
            Dictionary containing:
            - total_files: Number of files processed
            - files_changed: Number of files with formatting changes
            - files_unchanged: Number of files already properly formatted
            - files_written: Number of files actually written (when overwrite=True)
            - results: List of per-file results with file, changed, written
            - errors: List of files that failed to process
            - unmatched_patterns: List of patterns that didn't match any files

        Example::

            format_files(["tests/**/*.robot"])  # Preview changes
            format_files(["tests/**/*.robot"], overwrite=True)  # Apply changes

        """
        if ctx:
            mode = "formatting and overwriting" if overwrite else "formatting (preview)"
            await ctx.info(f"{mode.capitalize()} {len(file_patterns)} pattern(s)...")

        result = _format_files_impl(file_patterns, base_path, select, space_count, line_length, overwrite=overwrite)

        if ctx:
            files_changed = result["files_changed"]
            files_written = result["files_written"]
            msg = f"Completed: {files_changed} file(s) changed"
            if overwrite:
                msg += f", {files_written} written"
            await ctx.info(msg)

        return result

    @mcp.tool(
        tags={"linting", "formatting"},
        annotations={
            "readOnlyHint": True,
            "idempotentHint": True,
            "title": "Format and Lint Code",
        },
    )
    async def lint_and_format(
        content: str,
        filename: str = "stdin.robot",
        lint_select: list[str] | None = None,
        lint_ignore: list[str] | None = None,
        threshold: str = "I",
        format_select: list[str] | None = None,
        space_count: int = 4,
        line_length: int = 120,
        limit: int | None = None,
        configure: list[str] | None = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Format Robot Framework code and lint the result in one operation.

        This is the recommended tool for cleaning up code - it formats first,
        then lints the formatted result to show remaining issues that need
        manual fixes.

        Args:
            content: Robot Framework source code to process
            filename: Virtual filename (affects parsing)
            lint_select: List of linter rule IDs/names to enable
            lint_ignore: List of linter rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            format_select: List of formatter names to apply (if empty, uses defaults)
            space_count: Number of spaces for indentation (default: 4)
            line_length: Maximum line length (default: 120)
            limit: Maximum number of issues to return (None = no limit)
            configure: List of rule configurations (e.g., ["line-too-long.line_length=140"])

        Returns:
            Dictionary containing:
            - formatted: The formatted source code
            - changed: Boolean indicating if formatting modified the code
            - diff: Unified diff if formatting changed, None otherwise
            - issues: List of remaining lint issues in the formatted code
            - issues_before: Number of issues before formatting
            - issues_after: Number of issues after formatting
            - issues_fixed: Number of issues fixed by formatting

        Example::

            lint_and_format(robot_code)
            # Returns: {"formatted": "...", "changed": True, "issues": [...], "issues_fixed": 5}

        """
        if ctx:
            await ctx.info(f"Processing content ({len(content)} bytes)...")

        # First, count issues in original code
        issues_before = _lint_content_impl(content, filename, lint_select, lint_ignore, threshold, configure=configure)

        if ctx:
            await ctx.info(f"Found {len(issues_before)} issue(s) before formatting")

        # Format the code
        format_result = _format_content_impl(content, filename, format_select, space_count, line_length)

        if ctx:
            if format_result["changed"]:
                await ctx.info("Formatting applied changes")
            else:
                await ctx.info("No formatting changes needed")

        # Lint the formatted code without limit first for accurate counts
        issues_after_full = _lint_content_impl(
            format_result["formatted"],
            filename,
            lint_select,
            lint_ignore,
            threshold,
            configure=configure,
        )
        issues_after_count = len(issues_after_full)

        # Apply limit only to the returned issues list
        issues_after = issues_after_full[:limit] if limit else issues_after_full

        if ctx:
            fixed = len(issues_before) - issues_after_count
            await ctx.info(f"Remaining issues: {issues_after_count} ({fixed} fixed by formatting)")

        return {
            "formatted": format_result["formatted"],
            "changed": format_result["changed"],
            "diff": format_result["diff"],
            "issues": issues_after,
            "issues_before": len(issues_before),
            "issues_after": issues_after_count,
            "issues_fixed": len(issues_before) - issues_after_count,
        }

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "List Linting Rules"},
    )
    async def list_rules(
        category: str | None = None,
        severity: str | None = None,
        enabled_only: bool = False,
        ctx: Context | None = None,
    ) -> list[dict]:
        """
        List all available linting rules with optional filtering.

        Use this tool to discover available rules before linting, or to find
        rules related to a specific category (e.g., naming, length, documentation).

        Args:
            category: Filter by rule category/group (e.g., "LEN", "NAME", "DOC", "SPACE")
            severity: Filter by severity ("I"=Info, "W"=Warning, "E"=Error)
            enabled_only: If True, only return rules that are enabled by default

        Returns:
            List of rule summaries, each containing:
            - rule_id: The rule ID (e.g., "LEN01")
            - name: The rule name (e.g., "too-long-keyword")
            - severity: Default severity (I/W/E)
            - enabled: Whether enabled by default
            - message: The rule message template

        Example:
            >>> list_rules(category="LEN")  # All length-related rules
            >>> list_rules(severity="E")  # All error-level rules
            >>> list_rules(enabled_only=True)  # Only enabled rules

        """
        if ctx:
            filters = []
            if category:
                filters.append(f"category={category}")
            if severity:
                filters.append(f"severity={severity}")
            if enabled_only:
                filters.append("enabled_only=True")
            filter_str = ", ".join(filters) if filters else "none"
            await ctx.debug(f"Listing rules with filters: {filter_str}")

        return _list_rules_impl(category, severity, enabled_only)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "List Formatters"},
    )
    async def list_formatters(enabled_only: bool = True, ctx: Context | None = None) -> list[dict]:
        """
        List all available formatters.

        Use this tool to discover available formatters before formatting code.
        Formatters automatically fix style issues in Robot Framework code.

        Args:
            enabled_only: If True (default), only return formatters enabled by default

        Returns:
            List of formatter summaries, each containing:
            - name: Formatter name
            - enabled: Whether enabled by default
            - description: Brief description of what the formatter does

        Example:
            >>> list_formatters()  # All enabled formatters
            >>> list_formatters(enabled_only=False)  # All formatters including disabled

        """
        if ctx:
            await ctx.debug(f"Listing formatters (enabled_only={enabled_only})")

        return _list_formatters_impl(enabled_only)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "Get Rule Details"},
    )
    async def get_rule_info(rule_name_or_id: str, ctx: Context | None = None) -> dict:
        """
        Get detailed documentation for a linting rule.

        Args:
            rule_name_or_id: Rule name (e.g., "too-long-keyword") or ID (e.g., "LEN01")

        Returns:
            Dictionary containing:
            - rule_id: The rule ID
            - name: The rule name
            - message: The rule message template
            - severity: Default severity (I/W/E)
            - enabled: Whether enabled by default
            - deprecated: Whether the rule is deprecated
            - docs: Full documentation
            - parameters: List of configurable parameters
            - added_in_version: Robocop version when rule was added
            - version_requirement: Robot Framework version requirement (if any)

        Example::

            get_rule_info("LEN01")
            get_rule_info("too-long-keyword")

        """
        if ctx:
            await ctx.debug(f"Looking up rule: {rule_name_or_id}")

        return _get_rule_info_impl(rule_name_or_id)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True, "title": "Get Formatter Details"},
    )
    async def get_formatter_info(formatter_name: str, ctx: Context | None = None) -> dict:
        """
        Get detailed documentation for a formatter.

        Args:
            formatter_name: Formatter name (e.g., "NormalizeSeparators", "AlignKeywordsSection")

        Returns:
            Dictionary containing:
            - name: Formatter name
            - enabled: Whether enabled by default
            - docs: Full documentation
            - min_version: Minimum Robot Framework version (if any)

        Example:
            >>> get_formatter_info("NormalizeSeparators")
            {"name": "NormalizeSeparators", "enabled": True, "docs": "...", ...}

        """
        if ctx:
            await ctx.debug(f"Looking up formatter: {formatter_name}")

        return _get_formatter_info_impl(formatter_name)

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True, "title": "Suggest Code Fixes"},
    )
    async def suggest_fixes(
        content: str,
        filename: str = "stdin.robot",
        rule_ids: list[str] | None = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Analyze Robot Framework code and suggest fixes for linting issues.

        This tool goes beyond just identifying issues - it provides actionable
        suggestions for how to fix each problem. Use this when you want guidance
        on resolving linting issues.

        Args:
            content: Robot Framework source code to analyze
            filename: Virtual filename (affects file type detection)
            rule_ids: Optional list of specific rule IDs to get suggestions for

        Returns:
            Dictionary containing:
            - fixes: List of fix suggestions, each with:
                - rule_id: The rule ID
                - name: The rule name
                - line: Line number
                - message: The issue description
                - suggestion: How to fix this issue
                - auto_fixable: Whether format_content can fix this automatically
            - total_issues: Total number of issues found
            - auto_fixable: Count of issues that can be auto-fixed by formatting
            - manual_required: Count of issues requiring manual fixes
            - recommendation: Overall recommendation for fixing

        Example:
            >>> suggest_fixes(robot_code)
            {"fixes": [...], "auto_fixable": 3, "manual_required": 2, ...}

        """
        if ctx:
            await ctx.info(f"Analyzing content for fix suggestions ({len(content)} bytes)...")

        result = _suggest_fixes_impl(content, filename, rule_ids)

        if ctx:
            await ctx.info(
                f"Found {result['total_issues']} issues: "
                f"{result['auto_fixable']} auto-fixable, {result['manual_required']} manual"
            )

        return result

    @mcp.tool(
        tags={"linting", "statistics"},
        annotations={"readOnlyHint": True, "title": "Get Codebase Statistics"},
    )
    async def get_statistics(
        directory_path: str,
        recursive: bool = True,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        configure: list[str] | None = None,
        ctx: Context | None = None,
    ) -> dict:
        """
        Get code quality statistics for a Robot Framework codebase.

        This tool provides a high-level overview of code quality including:
        - Total files and issues count
        - Issue breakdown by severity
        - Most common issues (top 10)
        - Quality score and grade
        - Actionable recommendations

        Use this to understand the overall health of a test suite before
        diving into specific issues.

        Args:
            directory_path: Absolute path to the directory to analyze
            recursive: Whether to search subdirectories (default: True)
            select: List of rule IDs/names to enable
            ignore: List of rule IDs/names to ignore
            threshold: Minimum severity to report (I=Info, W=Warning, E=Error)
            configure: List of rule configurations

        Returns:
            Dictionary containing:
            - directory: The analyzed directory path
            - summary: Overview stats (total_files, files_with_issues, files_clean,
              total_issues, avg_issues_per_file, max_issues_in_file)
            - severity_breakdown: Issues by severity {E: count, W: count, I: count}
            - top_issues: List of most common rules with counts
            - quality_score: Score (0-100), grade (A-F), and label
            - recommendations: List of actionable suggestions

        Example::

            get_statistics("/path/to/tests")
            # Returns: {"quality_score": {"score": 85, "grade": "B", ...}, ...}

        """
        if ctx:
            await ctx.info(f"Analyzing codebase: {directory_path}")

        result = _get_statistics_impl(directory_path, recursive, select, ignore, threshold, configure=configure)

        if ctx:
            score = result["quality_score"]
            await ctx.info(f"Quality score: {score['score']}/100 (Grade: {score['grade']})")

        return result

    @mcp.tool(
        tags={"linting", "documentation"},
        annotations={"readOnlyHint": True, "title": "Explain Issue at Line"},
    )
    async def explain_issue(
        content: str,
        line: int,
        filename: str = "stdin.robot",
        context_lines: int = 3,
        ctx: Context | None = None,
    ) -> dict:
        """
        Explain a specific issue at a given line with surrounding context.

        This tool provides detailed explanations for issues at a specific line,
        including why the issue matters, how to fix it, and configurable parameters.
        More detailed than get_rule_info because it shows the actual code context.

        Args:
            content: Robot Framework source code to analyze
            line: The line number to explain (1-indexed)
            filename: Virtual filename (affects file type detection)
            context_lines: Number of lines to show before/after (default: 3)

        Returns:
            Dictionary containing:
            - line: The requested line number
            - issues_found: Boolean indicating if issues were found
            - issues: List of detailed explanations for issues at this line, each with:
                - rule_id, name, message, severity
                - why_it_matters: First line of rule documentation
                - fix_suggestion: How to fix this issue
                - full_documentation: Complete rule docs
                - configurable_parameters: List of parameters that can be adjusted
            - related_issues: Issues on nearby lines (within 2 lines)
            - context: The surrounding code with line numbers

        Example::

            explain_issue(robot_code, line=42)
            # Returns detailed explanation of issues at line 42 with context

        """
        if ctx:
            await ctx.info(f"Explaining issues at line {line}...")

        result = _explain_issue_impl(content, line, filename, context_lines)

        if ctx:
            if result["issues_found"]:
                count = len(result.get("issues", []))
                await ctx.info(f"Found {count} issue(s) at line {line}")
            else:
                await ctx.info(f"No issues found at or near line {line}")

        return result
