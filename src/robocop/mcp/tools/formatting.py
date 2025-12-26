"""Core formatting functionality for MCP tools."""

from __future__ import annotations

from difflib import unified_diff
from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError
from robot.api import get_model
from robot.errors import DataError

from robocop.config import FormatterConfig, WhitespaceConfig
from robocop.formatter import disablers
from robocop.formatter.utils import misc
from robocop.mcp.tools.utils.constants import VALID_EXTENSIONS
from robocop.mcp.tools.utils.helpers import _normalize_suffix, _temp_robot_file


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


def _format_file_impl(
    file_path: str,
    select: list[str] | None = None,
    space_count: int = 4,
    line_length: int = 120,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Format a Robot Framework file.

    Args:
        file_path: Path to the file to format.
        select: List of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        overwrite: Whether to overwrite the file with formatted content.

    Returns:
        A dictionary containing the formatting result.

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
        result = _format_content_impl(content, path.name, select, space_count, line_length)

        # Optionally overwrite the file
        if overwrite and result["changed"]:
            path.write_text(result["formatted"], encoding="utf-8")
            result["written"] = True
        else:
            result["written"] = False

        result["file"] = str(path)
        return result

    except OSError as e:
        raise ToolError(f"Failed to read/write file: {e}") from e
