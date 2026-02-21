"""Core formatting functionality for MCP tools."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import cast

from fastmcp.exceptions import ToolError
from robot.api import get_model
from robot.errors import DataError

from robocop.config.manager import ConfigManager
from robocop.config.schema import RawConfig, RawFormatterConfig, RawWhitespaceConfig
from robocop.formatter import disablers
from robocop.mcp.tools.models import FormatContentResult, FormatFileResult, LintAndFormatResult
from robocop.mcp.tools.utils.constants import VALID_EXTENSIONS
from robocop.mcp.tools.utils.helpers import _normalize_suffix, _temp_robot_file
from robocop.runtime.resolver import ConfigResolver
from robocop.source_file import StatementLinesCollector


def _format_content_impl(
    content: str,
    filename: str = "stdin.robot",
    select: list[str] | None = None,
    space_count: int | None = None,
    line_length: int | None = None,
    config_path: Path | None = None,
) -> FormatContentResult:
    """
    Format content and return the result.

    Args:
        content: The Robot Framework source code to format.
        filename: The virtual filename (affects parsing).
        select: A list of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        config_path: Path to the Robocop toml configuration file

    Returns:
        A FormatContentResult model containing formatted code, changed flag, and diff.

    Raises:
        ToolError: If the content cannot be parsed.

    """
    suffix = _normalize_suffix(filename)

    with _temp_robot_file(content, suffix) as tmp_path:
        try:
            model = get_model(str(tmp_path))
            # FIXME: why we are doing it manually when we can reuse runnner class, just with proper config management
            # also we overwrite any config values user may have
            # and keeping it here means we have to maintain 2 places - can we create common for it?
            whitespace_config = RawWhitespaceConfig(space_count=space_count, line_length=line_length)
            formatter_config = RawFormatterConfig(
                select=select, whitespace_config=whitespace_config, overwrite=False, return_result=True
            )
            raw_config = RawConfig(formatter=formatter_config, silent=True)

            config_manager = ConfigManager(sources=[str(tmp_path)], overwrite_config=raw_config, config=config_path)
            config = config_manager.default_config
            resolved_config = ConfigResolver(load_formatters=True).resolve_config(config)

            old_model = StatementLinesCollector(model)

            disabler_finder = disablers.RegisterDisablers(
                config.formatter.start_line,
                config.formatter.end_line,
            )
            disabler_finder.visit(model)

            for name, formatter in resolved_config.formatters.items():
                formatter.disablers = disabler_finder.disablers
                if not disabler_finder.disablers.is_disabled_in_file(name):
                    formatter.visit(model)

            new_model = StatementLinesCollector(model)
            changed = new_model != old_model

            diff_text = None
            if changed:
                old_lines = old_model.text.splitlines(keepends=True)
                new_lines = new_model.text.splitlines(keepends=True)
                diff_text = "".join(unified_diff(old_lines, new_lines, fromfile="before", tofile="after"))

            return FormatContentResult(formatted=new_model.text, changed=changed, diff=diff_text)

        except DataError as e:
            raise ToolError(f"Failed to parse Robot Framework content: {e}") from e


def _format_file_impl(
    file_path: str,
    select: list[str] | None = None,
    space_count: int | None = None,
    line_length: int | None = None,
    *,
    overwrite: bool = False,
    config_path: Path | None = None,
) -> FormatFileResult:
    """
    Format a Robot Framework file.

    Args:
        file_path: Path to the file to format.
        select: List of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        overwrite: Whether to overwrite the file with formatted content.
        config_path: Path to the Robocop toml configuration file

    Returns:
        A FormatFileResult model containing the formatting result.

    Raises:
        ToolError: If the file does not exist or is of invalid type.

    """
    path = Path(file_path)

    if not path.exists():
        raise ToolError(f"File not found: {file_path}")

    if path.suffix not in VALID_EXTENSIONS:
        raise ToolError(f"Invalid file type: {path.suffix}. Expected .robot or .resource file.")

    try:
        # Read the file content
        content = path.read_text(encoding="utf-8")

        # Format using existing implementation
        format_result = _format_content_impl(
            content, path.name, select, space_count, line_length, config_path=config_path
        )

        # Optionally overwrite the file
        written = False
        if overwrite and format_result.changed:
            path.write_text(format_result.formatted, encoding="utf-8")
            written = True

        return FormatFileResult(
            formatted=format_result.formatted,
            changed=format_result.changed,
            diff=format_result.diff,
            file=str(path),
            written=written,
        )

    except OSError as e:
        raise ToolError(f"Failed to read/write file: {e}") from e


def _lint_and_format_impl(
    content: str | None = None,
    file_path: str | None = None,
    filename: str = "stdin.robot",
    lint_select: list[str] | None = None,
    lint_ignore: list[str] | None = None,
    threshold: str = "I",
    format_select: list[str] | None = None,
    space_count: int | None = None,
    line_length: int | None = None,
    limit: int | None = None,
    configure: list[str] | None = None,
    *,
    overwrite: bool = False,
    config_path: Path | None = None,
) -> LintAndFormatResult:
    """
    Format Robot Framework code and lint the result in one operation.

    Args:
        content: Robot Framework source code to process (use this OR file_path).
        file_path: Path to the file to process (use this OR content).
        filename: Virtual filename when using content (affects parsing).
        lint_select: List of linter rule IDs/names to enable.
        lint_ignore: List of linter rule IDs/names to ignore.
        threshold: Minimum severity to report (I=Info, W=Warning, E=Error).
        format_select: List of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        limit: Maximum number of issues to return.
        configure: List of rule configurations.
        overwrite: Whether to overwrite the file with formatted content (only when file_path is used).
        config_path: Path to the Robocop toml configuration file

    Returns:
        A LintAndFormatResult model containing the lint and format results.

    Raises:
        ToolError: If neither content nor file_path is provided, or if both are provided.

    """
    from robocop.mcp.tools.linting import _lint_content_impl

    # Validate input - must have exactly one of content or file_path
    if content is None and file_path is None:
        raise ToolError("Either 'content' or 'file_path' must be provided.")
    if content is not None and file_path is not None:
        raise ToolError("Provide either 'content' or 'file_path', not both.")

    # If file_path is provided, read the file and set filename
    source_file = None
    if file_path is not None:
        path = Path(file_path)

        if not path.exists():
            raise ToolError(f"File not found: {file_path}")

        if path.suffix not in VALID_EXTENSIONS:
            raise ToolError(f"Invalid file type: {path.suffix}. Expected .robot or .resource file.")

        try:
            content = path.read_text(encoding="utf-8")
            filename = path.name
            source_file = str(path)
        except OSError as e:
            raise ToolError(f"Failed to read file: {e}") from e
    content = cast("str", content)

    # Count issues in original code
    issues_before = _lint_content_impl(
        content, filename, lint_select, lint_ignore, threshold, configure=configure, config_path=config_path
    )

    # Format the code
    format_result = _format_content_impl(
        content, filename, format_select, space_count, line_length, config_path=config_path
    )

    # Lint the formatted code without limit first for accurate counts
    issues_after_full = _lint_content_impl(
        format_result.formatted,
        filename,
        lint_select,
        lint_ignore,
        threshold,
        configure=configure,
        config_path=config_path,
    )
    issues_after_count = len(issues_after_full)

    # Apply limit only to the returned issues list
    issues_after = list(issues_after_full[:limit]) if limit else list(issues_after_full)

    # Handle file-specific fields
    written = None
    if source_file is not None:
        # Optionally overwrite the file
        if overwrite and format_result.changed:
            try:
                Path(source_file).write_text(format_result.formatted, encoding="utf-8")
                written = True
            except OSError as e:
                raise ToolError(f"Failed to write file: {e}") from e
        else:
            written = False

    return LintAndFormatResult(
        formatted=format_result.formatted,
        changed=format_result.changed,
        diff=format_result.diff,
        issues=issues_after,
        issues_before=len(issues_before),
        issues_after=issues_after_count,
        issues_fixed=len(issues_before) - issues_after_count,
        file=source_file,
        written=written,
    )
