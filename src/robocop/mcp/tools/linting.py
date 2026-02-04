"""Core linting functionality for MCP tools."""

from __future__ import annotations

from pathlib import Path

from fastmcp.exceptions import ToolError
from robot.errors import DataError

from robocop.config.manager import ConfigManager
from robocop.config.schema import RawConfig, RawLinterConfig
from robocop.mcp.tools.models import DiagnosticResult
from robocop.mcp.tools.utils.constants import VALID_EXTENSIONS
from robocop.mcp.tools.utils.helpers import (
    _diagnostic_to_dict,
    _normalize_suffix,
    _parse_threshold,
    _temp_robot_file,
)
from robocop.source_file import SourceFile


def _create_linter_config(
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    configure: list[str] | None = None,
) -> RawLinterConfig:
    """Create a RawConfig with the given options."""
    return RawLinterConfig(
        select=select or [],
        ignore=ignore or [],
        configure=configure or [],
        threshold=_parse_threshold(threshold),
        return_result=True,
    )


def _lint_content_impl(
    content: str,
    filename: str = "stdin.robot",
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    limit: int | None = None,
    configure: list[str] | None = None,
) -> list[DiagnosticResult]:
    """
    Lint content and return diagnostics.

    Args:
        content: The Robot Framework source code to lint.
        filename: The virtual filename (affects parsing).
        select: A list of rule IDs to select.
        ignore: A list of rule IDs to ignore.
        threshold: The severity threshold for diagnostics.
        limit: Maximum number of issues to return. None means no limit.
        configure: A list of rule configurations (e.g., ["rule-name.param=value"]).

    Returns:
        A list of DiagnosticResult models.

    Raises:
        ToolError: If the content cannot be parsed.

    """
    from robocop.linter.runner import RobocopLinter

    suffix = _normalize_suffix(filename)

    with _temp_robot_file(content, suffix) as tmp_path:
        try:
            linter_config = _create_linter_config(select, ignore, threshold, configure)
            config = RawConfig(sources=[str(tmp_path)], linter=linter_config, silent=True)
            config_manager = ConfigManager(
                sources=[str(tmp_path)],
                ignore_file_config=True,
                overwrite_config=config,
            )

            linter = RobocopLinter(config_manager)
            # FIXME it should find config for specific file, not just some random. and those overwrites
            # for now config -> default_config
            source_file = SourceFile(path=tmp_path, config=config_manager.default_config)
            diagnostics = linter.run_check(source_file)

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
    configure: list[str] | None = None,
) -> list[DiagnosticResult]:
    """
    Lint a file and return diagnostics.

    Args:
        file_path: The path to the file to lint.
        select: A list of rule IDs to select.
        ignore: A list of rule IDs to ignore.
        threshold: The severity threshold for diagnostics.
        include_file_in_result: Whether to include the file path in the result.
        limit: Maximum number of issues to return. None means no limit.
        configure: A list of rule configurations (e.g., ["rule-name.param=value"]).

    Returns:
        A list of DiagnosticResult models.

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
        linter_config = _create_linter_config(select, ignore, threshold, configure)
        config = RawConfig(sources=[str(path)], linter=linter_config, silent=True)
        config_manager = ConfigManager(
            sources=[str(path)],
            ignore_file_config=True,
            overwrite_config=config,
        )

        linter = RobocopLinter(config_manager)
        # FIXME, and what's the diff from _lint_content_impl -> could be merged
        source_file = SourceFile(path=path, config=config_manager.default_config)
        diagnostics = linter.run_check(source_file)

        file_str = str(path) if include_file_in_result else None
        result = [_diagnostic_to_dict(d, file_str) for d in diagnostics]
        return result[:limit] if limit else result

    except DataError as e:
        raise ToolError(f"Failed to parse Robot Framework file: {e}") from e
