"""Batch file operations for MCP tools - handles glob patterns and multiple files."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.formatting import _format_file_impl
from robocop.mcp.tools.linting import _lint_file_impl
from robocop.mcp.tools.utils.constants import GLOB_CHARS, VALID_EXTENSIONS, VALID_GROUP_BY


def _is_glob_pattern(pattern: str) -> bool:
    """Check if a string contains glob pattern characters."""
    return any(c in GLOB_CHARS for c in pattern)


def _expand_file_patterns(
    patterns: list[str],
    base_path: Path | None = None,
) -> tuple[list[Path], list[str]]:
    """
    Expand file paths and glob patterns to a deduplicated list of Robot Framework files.

    Args:
        patterns: List of file paths or glob patterns (e.g., ["test.robot", "tests/**/*.robot"])
        base_path: Optional base directory for relative paths/globs. Defaults to current directory.

    Returns:
        A tuple of (resolved_files, unmatched_patterns):
        - resolved_files: Deduplicated, sorted list of existing .robot/.resource files
        - unmatched_patterns: List of patterns that didn't match any valid files

    """
    if base_path is None:
        base_path = Path.cwd()

    resolved_files: set[Path] = set()
    unmatched_patterns: list[str] = []

    for pattern in patterns:
        matched = False

        if _is_glob_pattern(pattern):
            # Glob pattern - expand using base_path.glob()
            for match in base_path.glob(pattern):
                if match.is_file() and match.suffix in VALID_EXTENSIONS:
                    resolved_files.add(match.resolve())
                    matched = True
        else:
            # Explicit file path
            path = Path(pattern)
            if not path.is_absolute():
                path = base_path / path

            if path.is_file() and path.suffix in VALID_EXTENSIONS:
                resolved_files.add(path.resolve())
                matched = True

        if not matched:
            unmatched_patterns.append(pattern)

    return sorted(resolved_files), unmatched_patterns


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


def _group_issues(
    issues: list[dict[str, Any]],
    group_by: str,
    limit_per_group: int | None = None,
) -> tuple[dict[str, list[dict[str, Any]]], dict[str, int]]:
    """
    Group issues by the specified field.

    Args:
        issues: Flat list of issues (each must have the grouping field)
        group_by: Field to group by ("severity", "rule", "file")
        limit_per_group: Max issues per group (None = no limit)

    Returns:
        Tuple of (grouped_issues, group_counts) where:
        - grouped_issues: Dict mapping group key to list of issues
        - group_counts: Dict mapping group key to total count (before limit)

    Raises:
        ToolError: If group_by is not a valid option.

    """
    if group_by not in VALID_GROUP_BY:
        raise ToolError(f"Invalid group_by '{group_by}'. Use: {', '.join(sorted(VALID_GROUP_BY))}")

    # Map group_by option to the issue field name
    field_map = {
        "severity": "severity",
        "rule": "rule_id",
        "file": "file",
    }
    field = field_map[group_by]

    # Group issues by the specified field
    groups: dict[str, list[dict[str, Any]]] = {}
    for issue in issues:
        key = issue.get(field, "unknown")
        if key not in groups:
            groups[key] = []
        groups[key].append(issue)

    # Calculate counts before applying limit
    group_counts = {key: len(items) for key, items in groups.items()}

    # Apply limit per group
    if limit_per_group is not None:
        groups = {key: items[:limit_per_group] for key, items in groups.items()}

    return groups, group_counts


def _lint_files_impl(
    file_patterns: list[str],
    base_path: str | None = None,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    limit: int | None = None,
    configure: list[str] | None = None,
    group_by: str | None = None,
) -> dict[str, Any]:
    """
    Lint multiple files specified by paths or glob patterns.

    Args:
        file_patterns: List of file paths or glob patterns.
        base_path: Base directory for resolving relative paths/patterns.
        select: A list of rule IDs to select.
        ignore: A list of rule IDs to ignore.
        threshold: The severity threshold for diagnostics.
        limit: Maximum number of issues to return. None means no limit.
            When group_by is set, limit applies per group.
        configure: A list of rule configurations.
        group_by: Optional grouping for results ("severity", "rule", "file").
            When set, issues are grouped and limit applies per group.

    Returns:
        A dictionary containing:
        - total_files: Number of files linted
        - total_issues: Total issues found (before limit)
        - files_with_issues: Number of files with at least one issue
        - issues: List of issues (each includes 'file' field), or dict if group_by is set
        - summary: Issues by severity {E: count, W: count, I: count}
        - limited: Whether results were truncated
        - unmatched_patterns: Patterns that didn't match any files
        - group_counts: (only when group_by is set) Total count per group before limit

    Raises:
        ToolError: If no valid files are found.

    """
    base = Path(base_path) if base_path else None
    files, unmatched = _expand_file_patterns(file_patterns, base)

    if not files:
        raise ToolError(
            f"No .robot or .resource files found matching patterns: {file_patterns}"
            + (f" (unmatched: {unmatched})" if unmatched else "")
        )

    all_issues: list[dict[str, Any]] = []
    files_with_issues = 0
    summary: dict[str, int] = {"E": 0, "W": 0, "I": 0}

    for file in files:
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
            pass

    total_issues = len(all_issues)

    # Handle grouping vs flat list
    if group_by:
        grouped_issues, group_counts = _group_issues(all_issues, group_by, limit)
        # Check if any group was limited
        limited = any(group_counts[k] > len(v) for k, v in grouped_issues.items())
        return {
            "total_files": len(files),
            "total_issues": total_issues,
            "files_with_issues": files_with_issues,
            "issues": grouped_issues,
            "summary": summary,
            "limited": limited,
            "unmatched_patterns": unmatched,
            "group_counts": group_counts,
        }

    # Flat list mode (original behavior)
    limited = limit is not None and total_issues > limit
    if limited:
        all_issues = all_issues[:limit]

    return {
        "total_files": len(files),
        "total_issues": total_issues,
        "files_with_issues": files_with_issues,
        "issues": all_issues,
        "summary": summary,
        "limited": limited,
        "unmatched_patterns": unmatched,
    }


def _format_files_impl(
    file_patterns: list[str],
    base_path: str | None = None,
    select: list[str] | None = None,
    space_count: int = 4,
    line_length: int = 120,
    *,
    overwrite: bool = False,
) -> dict[str, Any]:
    """
    Format multiple Robot Framework files.

    Args:
        file_patterns: List of file paths or glob patterns.
        base_path: Base directory for resolving relative paths/patterns.
        select: List of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        overwrite: Whether to overwrite files with formatted content.

    Returns:
        A dictionary containing the formatting results.

    Raises:
        ToolError: If no valid files are found.

    """
    base = Path(base_path) if base_path else None
    files, unmatched = _expand_file_patterns(file_patterns, base)

    if not files:
        raise ToolError(
            f"No .robot or .resource files found matching patterns: {file_patterns}"
            + (f" (unmatched: {unmatched})" if unmatched else "")
        )

    results: list[dict[str, Any]] = []
    files_changed = 0
    files_unchanged = 0
    files_written = 0
    errors: list[dict[str, str]] = []

    for file in files:
        try:
            result = _format_file_impl(str(file), select, space_count, line_length, overwrite=overwrite)
            results.append(
                {
                    "file": str(file),
                    "changed": result["changed"],
                    "written": result["written"],
                }
            )
            if result["changed"]:
                files_changed += 1
                if result["written"]:
                    files_written += 1
            else:
                files_unchanged += 1
        except ToolError as e:
            errors.append({"file": str(file), "error": str(e)})

    return {
        "total_files": len(files),
        "files_changed": files_changed,
        "files_unchanged": files_unchanged,
        "files_written": files_written,
        "results": results,
        "errors": errors,
        "unmatched_patterns": unmatched,
    }
