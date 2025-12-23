"""MCP Tools for Robocop - Linting and formatting tools exposed via MCP."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ToolError
from fastmcp.server.context import Context
from robot.api import get_model
from robot.errors import DataError

from robocop.config import Config, ConfigManager, FormatterConfig, LinterConfig
from robocop.formatter import disablers
from robocop.formatter.utils import misc
from robocop.linter.rules import RuleSeverity

if TYPE_CHECKING:
    from collections.abc import Generator

    from fastmcp import FastMCP

    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.rules import Rule, RuleParam

# Valid Robot Framework file extensions
VALID_EXTENSIONS = frozenset((".robot", ".resource"))

# Threshold string to severity mapping
THRESHOLD_MAP = {
    "I": RuleSeverity.INFO,
    "W": RuleSeverity.WARNING,
    "E": RuleSeverity.ERROR,
}


def _diagnostic_to_dict(diagnostic: Diagnostic, file_path: str | None = None) -> dict[str, Any]:
    """
    Convert a Diagnostic object to a dictionary for JSON serialization.

    Args:
        diagnostic: The Diagnostic object to convert.
        file_path: Optional file path to include in the result.

    Returns:
        A dictionary representation of the diagnostic.

    """
    result = {
        "rule_id": diagnostic.rule.rule_id,
        "name": diagnostic.rule.name,
        "message": diagnostic.message,
        "severity": diagnostic.severity.value,
        "line": diagnostic.range.start.line,
        "column": diagnostic.range.start.character,
        "end_line": diagnostic.range.end.line,
        "end_column": diagnostic.range.end.character,
    }
    if file_path:
        result["file"] = file_path
    return result


def _param_to_dict(param: RuleParam) -> dict[str, Any]:
    """
    Convert a RuleParam to a dictionary.

    Args:
        param: The RuleParam to convert.

    Returns:
        A dictionary representation of the parameter.

    """
    return {
        "name": param.name,
        "default": str(param.raw_value) if param.raw_value is not None else None,
        "description": param.desc,
        "type": param.param_type,
    }


def _rule_to_dict(rule: Rule) -> dict[str, Any]:
    """
    Convert a Rule to a detailed dictionary.

    Args:
        rule: The Rule to convert.

    Returns:
        A dictionary representation of the rule.

    """
    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "message": rule.message,
        "severity": rule.severity.value,
        "enabled": rule.enabled,
        "deprecated": rule.deprecated,
        "docs": rule.docs,
        "parameters": ([_param_to_dict(p) for p in rule.parameters] if rule.parameters else []),
        "added_in_version": rule.added_in_version,
        "version_requirement": rule.version or None,
    }


def _parse_threshold(threshold: str) -> RuleSeverity:
    """
    Parse threshold string to RuleSeverity.

    Args:
        threshold: Threshold string ("I", "W", or "E")

    Returns:
        RuleSeverity: Corresponding RuleSeverity enum value.

    Raises:
        ToolError: If the threshold is invalid.

    """
    try:
        return THRESHOLD_MAP[threshold.upper()]
    except KeyError:
        raise ToolError(f"Invalid threshold '{threshold}'. Use I (Info), W (Warning), or E (Error).") from None


def _normalize_suffix(filename: str) -> str:
    """
    Normalize file suffix to a valid Robot Framework extension.

    Args:
        filename: The filename to check.

    Returns:
        The valid file suffix (".robot" or ".resource"). Defaults to ".robot" if invalid.

    """
    suffix = Path(filename).suffix or ".robot"
    return suffix if suffix in VALID_EXTENSIONS else ".robot"


@contextmanager
def _temp_robot_file(content: str, suffix: str) -> Generator[Path, None, None]:
    """
    Create a temporary Robot Framework file and clean up after use.

    Args:
        content: The content to write to the temporary file.
        suffix: The file suffix (".robot" or ".resource").

    Yields:
        The path to the temporary file.

    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def _create_linter_config(
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
) -> LinterConfig:
    """Create a LinterConfig with the given options."""
    return LinterConfig(
        select=select or [],
        ignore=ignore or [],
        threshold=_parse_threshold(threshold),
        return_result=True,
        silent=True,
    )


def _lint_content_impl(
    content: str,
    filename: str = "stdin.robot",
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Lint content and return diagnostics.

    Args:
        content: The Robot Framework source code to lint.
        filename: The virtual filename (affects parsing).
        select: A list of rule IDs to select.
        ignore: A list of rule IDs to ignore.
        threshold: The severity threshold for diagnostics.
        limit: Maximum number of issues to return. None means no limit.

    Returns:
        A list of dictionaries representing the diagnostics.

    Raises:
        ToolError: If the content cannot be parsed.

    """
    from robocop.linter.runner import RobocopLinter

    suffix = _normalize_suffix(filename)

    with _temp_robot_file(content, suffix) as tmp_path:
        try:
            linter_config = _create_linter_config(select, ignore, threshold)
            config = Config(sources=[str(tmp_path)], linter=linter_config, silent=True)
            config_manager = ConfigManager(
                sources=[str(tmp_path)],
                ignore_file_config=True,
                overwrite_config=config,
            )

            linter = RobocopLinter(config_manager)
            model = linter.get_model_for_file_type(tmp_path, language=None)
            diagnostics = linter.run_check(model, tmp_path, config, in_memory_content=content)

            result = [_diagnostic_to_dict(d) for d in diagnostics]
            return result[:limit] if limit else result

        except DataError as e:
            raise ToolError(f"Failed to parse Robot Framework content: {e}") from e


def _lint_file_impl(
    file_path: str,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    include_file_in_result: bool = False,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Lint a file and return diagnostics.

    Args:
        file_path: The path to the file to lint.
        select: A list of rule IDs to select.
        ignore: A list of rule IDs to ignore.
        threshold: The severity threshold for diagnostics.
        include_file_in_result: Whether to include the file path in the result.
        limit: Maximum number of issues to return. None means no limit.

    Returns:
        A list of dictionaries representing the diagnostics.

    Raises:
        ToolError: If the file does not exist or is of invalid type.

    """
    from robocop.linter.runner import RobocopLinter

    path = Path(file_path)

    if not path.exists():
        raise ToolError(f"File not found: {file_path}")

    if path.suffix not in VALID_EXTENSIONS:
        raise ToolError(f"Invalid file type: {path.suffix}. Expected .robot or .resource file.")

    try:
        linter_config = _create_linter_config(select, ignore, threshold)
        config = Config(sources=[str(path)], linter=linter_config, silent=True)
        config_manager = ConfigManager(
            sources=[str(path)],
            ignore_file_config=True,
            overwrite_config=config,
        )

        linter = RobocopLinter(config_manager)
        model = linter.get_model_for_file_type(path, language=None)
        diagnostics = linter.run_check(model, path, config)

        file_str = str(path) if include_file_in_result else None
        result = [_diagnostic_to_dict(d, file_str) for d in diagnostics]
        return result[:limit] if limit else result

    except DataError as e:
        raise ToolError(f"Failed to parse Robot Framework file: {e}") from e


def _collect_robot_files(directory: Path, recursive: bool = True) -> list[Path]:
    """
    Collect all Robot Framework files in a directory.

    Args:
        directory: The directory to search.
        recursive: Whether to search recursively.

    Returns:
        A list of Path objects for all Robot Framework files in the directory.

    """
    files = []
    pattern = "**/*" if recursive else "*"
    for ext in VALID_EXTENSIONS:
        files.extend(directory.glob(f"{pattern}{ext}"))
    return sorted(files)


def _format_content_impl(
    content: str,
    filename: str = "stdin.robot",
    select: list[str] | None = None,
    space_count: int = 4,
    line_length: int = 120,
) -> dict[str, Any]:
    """
    Format content and return the result.

    Args:
        content: The Robot Framework source code to format.
        filename: The virtual filename (affects parsing).
        select: A list of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.

    Returns:
        A dictionary containing:
        - formatted: The formatted source code.
        - changed: Boolean indicating if content was modified.
        - diff: Unified diff if content changed, None otherwise.

    Raises:
        ToolError: If the content cannot be parsed.

    """
    from robocop.config import WhitespaceConfig

    suffix = _normalize_suffix(filename)

    with _temp_robot_file(content, suffix) as tmp_path:
        try:
            model = get_model(str(tmp_path))

            whitespace_config = WhitespaceConfig(space_count=space_count, line_length=line_length)
            formatter_config = FormatterConfig(
                select=select or [],
                whitespace_config=whitespace_config,
                overwrite=False,
                return_result=True,
                silent=True,
            )

            old_model = misc.StatementLinesCollector(model)

            disabler_finder = disablers.RegisterDisablers(
                formatter_config.start_line,
                formatter_config.end_line,
            )
            disabler_finder.visit(model)

            for name, formatter in formatter_config.formatters.items():
                formatter.disablers = disabler_finder.disablers
                if not disabler_finder.disablers.is_disabled_in_file(name):
                    formatter.visit(model)

            new_model = misc.StatementLinesCollector(model)
            changed = new_model != old_model

            diff_text = None
            if changed:
                old_lines = [line + "\n" for line in old_model.text.splitlines()]
                new_lines = [line + "\n" for line in new_model.text.splitlines()]
                diff_text = "".join(unified_diff(old_lines, new_lines, fromfile="before", tofile="after"))

            return {"formatted": new_model.text, "changed": changed, "diff": diff_text}

        except DataError as e:
            raise ToolError(f"Failed to parse Robot Framework content: {e}") from e


def _get_rule_info_impl(rule_name_or_id: str) -> dict[str, Any]:
    """
    Look up rule information by name or ID.

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

    Raises:
        ToolError: If the rule is not found.

    """
    from robocop.mcp.cache import get_linter_config

    linter_config = get_linter_config()

    if rule_name_or_id not in linter_config.rules:
        available = ", ".join(sorted({r.rule_id for r in linter_config.rules.values()}))
        raise ToolError(
            f"Rule '{rule_name_or_id}' not found. "
            f"Use rule ID (e.g., 'LEN01') or name (e.g., 'too-long-keyword'). "
            f"Available rule IDs: {available[:200]}..."
        )

    return _rule_to_dict(linter_config.rules[rule_name_or_id])


def _get_formatter_info_impl(formatter_name: str) -> dict[str, Any]:
    """
    Look up formatter information by name.

    Args:
        formatter_name: Formatter name (e.g., "NormalizeSeparators", "AlignKeywordsSection

    Returns:
        Dictionary containing:
        - name: Formatter name
        - enabled: Whether enabled by default
        - docs: Full documentation
        - min_version: Minimum Robot Framework version (if any)

    Raises:
        ToolError: If the formatter is not found.

    """
    from robocop.mcp.cache import get_formatter_config

    formatter_config = get_formatter_config()
    formatters = formatter_config.formatters

    if formatter_name not in formatters:
        available = ", ".join(sorted(formatters.keys()))
        raise ToolError(f"Formatter '{formatter_name}' not found. Available formatters: {available}")

    formatter = formatters[formatter_name]
    return {
        "name": formatter_name,
        "enabled": getattr(formatter, "ENABLED", True),
        "docs": formatter.__doc__ or "No documentation available.",
        "min_version": getattr(formatter, "MIN_VERSION", None),
    }


def register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools with the server."""

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True},
    )
    async def lint_content(
        content: str,
        filename: str = "stdin.robot",
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
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

        """
        if ctx:
            await ctx.info(f"Linting content ({len(content)} bytes)...")

        result = _lint_content_impl(content, filename, select, ignore, threshold, limit)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True},
    )
    async def lint_file(
        file_path: str,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
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

        Returns:
            List of diagnostic issues found (same format as lint_content)

        """
        if ctx:
            await ctx.info(f"Linting file: {file_path}")

        result = _lint_file_impl(file_path, select, ignore, threshold, limit=limit)

        if ctx:
            await ctx.info(f"Found {len(result)} issue(s)")

        return result

    @mcp.tool(
        tags={"linting"},
        annotations={"readOnlyHint": True},
    )
    async def lint_directory(
        directory_path: str,
        recursive: bool = True,
        select: list[str] | None = None,
        ignore: list[str] | None = None,
        threshold: str = "I",
        limit: int | None = None,
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
            limit: Maximum total number of issues to return across all files (None = no limit)

        Returns:
            Dictionary containing:
            - total_files: Number of files linted
            - total_issues: Total number of issues found (may be less than actual if limited)
            - files_with_issues: Number of files that have issues
            - issues: List of all issues (each includes 'file' field)
            - summary: Issues grouped by severity {E: count, W: count, I: count}
            - limited: Boolean indicating if results were truncated due to limit

        Raises:
            ToolError: If the directory does not exist or contains no Robot Framework files

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
        limited = False

        for i, file in enumerate(files):
            if ctx:
                await ctx.report_progress(progress=i, total=len(files))

            # Check if we've hit the limit
            if limit and len(all_issues) >= limit:
                limited = True
                break

            try:
                issues = _lint_file_impl(
                    str(file),
                    select,
                    ignore,
                    threshold,
                    include_file_in_result=True,
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

        # Apply limit to final results
        if limit and len(all_issues) > limit:
            all_issues = all_issues[:limit]
            limited = True

        if ctx:
            await ctx.report_progress(progress=len(files), total=len(files))
            msg = f"Completed: {len(all_issues)} issue(s) in {files_with_issues} file(s)"
            if limited:
                msg += f" (limited to {limit})"
            await ctx.info(msg)

        return {
            "total_files": len(files),
            "total_issues": len(all_issues),
            "files_with_issues": files_with_issues,
            "issues": all_issues,
            "summary": summary,
            "limited": limited,
        }

    @mcp.tool(
        tags={"formatting"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
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

        """
        if ctx:
            await ctx.info(f"Formatting content ({len(content)} bytes)...")

        result = _format_content_impl(content, filename, select, space_count, line_length)

        if ctx:
            status = "Content modified" if result["changed"] else "No changes needed"
            await ctx.info(status)

        return result

    @mcp.tool(
        tags={"linting", "formatting"},
        annotations={"readOnlyHint": True, "idempotentHint": True},
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

        Returns:
            Dictionary containing:
            - formatted: The formatted source code
            - changed: Boolean indicating if formatting modified the code
            - diff: Unified diff if formatting changed, None otherwise
            - issues: List of remaining lint issues in the formatted code
            - issues_before: Number of issues before formatting
            - issues_after: Number of issues after formatting
            - issues_fixed: Number of issues fixed by formatting

        """
        if ctx:
            await ctx.info(f"Processing content ({len(content)} bytes)...")

        # First, count issues in original code
        issues_before = _lint_content_impl(content, filename, lint_select, lint_ignore, threshold)

        if ctx:
            await ctx.info(f"Found {len(issues_before)} issue(s) before formatting")

        # Format the code
        format_result = _format_content_impl(content, filename, format_select, space_count, line_length)

        if ctx:
            if format_result["changed"]:
                await ctx.info("Formatting applied changes")
            else:
                await ctx.info("No formatting changes needed")

        # Lint the formatted code (apply limit here)
        issues_after = _lint_content_impl(
            format_result["formatted"], filename, lint_select, lint_ignore, threshold, limit
        )

        if ctx:
            fixed = len(issues_before) - len(issues_after)
            await ctx.info(f"Remaining issues: {len(issues_after)} ({fixed} fixed by formatting)")

        return {
            "formatted": format_result["formatted"],
            "changed": format_result["changed"],
            "diff": format_result["diff"],
            "issues": issues_after,
            "issues_before": len(issues_before),
            "issues_after": len(issues_after),
            "issues_fixed": len(issues_before) - len(issues_after),
        }

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True},
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

        """
        if ctx:
            await ctx.debug(f"Looking up rule: {rule_name_or_id}")

        return _get_rule_info_impl(rule_name_or_id)

    @mcp.tool(
        tags={"documentation"},
        annotations={"readOnlyHint": True},
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

        """
        if ctx:
            await ctx.debug(f"Looking up formatter: {formatter_name}")

        return _get_formatter_info_impl(formatter_name)
