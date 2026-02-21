"""Batch file operations for MCP tools - handles glob patterns and multiple files."""

from __future__ import annotations

from pathlib import Path

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.formatting import _format_file_impl
from robocop.mcp.tools.linting import _lint_file_impl
from robocop.mcp.tools.models import (
    DiagnosticResult,
    FormatFileInfo,
    FormatFilesResult,
    LintFilesResult,
    SeveritySummary,
    TopRule,
)
from robocop.mcp.tools.utils.constants import GLOB_CHARS, VALID_EXTENSIONS, VALID_GROUP_BY


def _is_glob_pattern(pattern: str) -> bool:
    """Check if a string contains glob pattern characters."""
    return any(c in GLOB_CHARS for c in pattern)


def _expand_extension_pattern(pattern: str) -> list[str]:
    """
    Expand a pattern to cover both .robot and .resource extensions.

    If pattern ends with .robot, also return .resource variant (and vice versa).
    If pattern ends with neither (e.g., "**/*"), return patterns for both extensions.

    Args:
        pattern: A file pattern (e.g., "**/*.robot", "tests/*", "file.robot")

    Returns:
        List of patterns covering both Robot Framework extensions.

    """
    if pattern.endswith(".robot"):
        # Also match .resource files with same pattern
        return [pattern, pattern[:-6] + ".resource"]
    if pattern.endswith(".resource"):
        # Also match .robot files with same pattern
        return [pattern, pattern[:-9] + ".robot"]
    if _is_glob_pattern(pattern) and not any(pattern.endswith(ext) for ext in VALID_EXTENSIONS):
        # Glob without extension (e.g., "**/*") - expand to both extensions
        # Remove trailing /* or * if present to avoid "**/*.robot" becoming "**/*/*.robot"
        if pattern.endswith("/*"):
            base = pattern[:-2]
            return [f"{base}/*.robot", f"{base}/*.resource"]
        if pattern.endswith("*"):
            base = pattern[:-1]
            return [f"{base}*.robot", f"{base}*.resource"]
        return [f"{pattern}/*.robot", f"{pattern}/*.resource"]
    # Explicit file path or pattern with specific extension
    return [pattern]


def _expand_file_patterns(
    patterns: list[str],
    base_path: Path | None = None,
) -> tuple[list[Path], list[str]]:
    """
    Expand file paths and glob patterns to a deduplicated list of Robot Framework files.

    Patterns ending with .robot will also match .resource files (and vice versa).
    Glob patterns without an extension (e.g., "**/*") will match both .robot and .resource.

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
        # Expand pattern to cover both .robot and .resource extensions
        expanded_patterns = _expand_extension_pattern(pattern)

        for expanded_pattern in expanded_patterns:
            if _is_glob_pattern(expanded_pattern):
                # Glob pattern - expand using base_path.glob()
                for match in base_path.glob(expanded_pattern):
                    if match.is_file() and match.suffix in VALID_EXTENSIONS:
                        resolved_files.add(match.resolve())
                        matched = True
            else:
                # Explicit file path
                path = Path(expanded_pattern)
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
    files: list[Path] = []
    pattern = "**/*" if recursive else "*"
    for ext in VALID_EXTENSIONS:
        files.extend(directory.glob(f"{pattern}{ext}"))
    return sorted(files)


def _group_issues(
    issues: list[DiagnosticResult],
    group_by: str,
    limit_per_group: int | None = None,
    offset_per_group: int = 0,
) -> tuple[dict[str, list[DiagnosticResult]], dict[str, int]]:
    """
    Group issues by the specified field.

    Args:
        issues: Flat list of DiagnosticResult models (each must have the grouping field)
        group_by: Field to group by ("severity", "rule", "file")
        limit_per_group: Max issues per group (None = no limit)
        offset_per_group: Number of issues to skip per group before applying limit

    Returns:
        Tuple of (grouped_issues, group_counts) where:
        - grouped_issues: Dict mapping group key to list of DiagnosticResult models
        - group_counts: Dict mapping group key to total count (before limit/offset)

    Raises:
        ToolError: If group_by is not a valid option.

    """
    if group_by not in VALID_GROUP_BY:
        raise ToolError(f"Invalid group_by '{group_by}'. Use: {', '.join(sorted(VALID_GROUP_BY))}")

    # Map group_by option to the issue attribute name
    field_map = {
        "severity": "severity",
        "rule": "rule_id",
        "file": "file",
    }
    field = field_map[group_by]

    # Group issues by the specified field
    groups: dict[str, list[DiagnosticResult]] = {}
    for issue in issues:
        key = getattr(issue, field, None) or "unknown"
        if key not in groups:
            groups[key] = []
        groups[key].append(issue)

    # Calculate counts before applying offset/limit
    group_counts = {key: len(items) for key, items in groups.items()}

    # Apply offset and limit per group
    if offset_per_group > 0 or limit_per_group is not None:
        result_groups: dict[str, list[DiagnosticResult]] = {}
        for key, items in groups.items():
            # Apply offset first
            offset_items = items[offset_per_group:] if offset_per_group > 0 else items
            # Then apply limit
            if limit_per_group is not None:
                offset_items = offset_items[:limit_per_group]
            result_groups[key] = offset_items
        groups = result_groups

    return groups, group_counts


def _lint_files_impl(
    file_patterns: list[str],
    base_path: str | None = None,
    select: list[str] | None = None,
    ignore: list[str] | None = None,
    threshold: str = "I",
    limit: int | None = None,
    offset: int = 0,
    configure: list[str] | None = None,
    group_by: str | None = None,
    summarize_only: bool = False,
    config_path: Path | None = None,
) -> LintFilesResult:
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
        offset: Number of issues to skip before applying limit (for pagination).
            When group_by is set, offset applies per group.
        configure: A list of rule configurations.
        group_by: Optional grouping for results ("severity", "rule", "file").
            When set, issues are grouped and limit/offset apply per group.
        summarize_only: If True, return only summary statistics without individual issues.
            Useful for large codebases to reduce response size.
        config_path: Path to the Robocop toml configuration file

    Returns:
        A LintFilesResult model containing linting results.

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

    all_issues: list[DiagnosticResult] = []
    files_with_issues = 0
    severity_counts = {"E": 0, "W": 0, "I": 0}

    for file in files:
        try:
            issues = _lint_file_impl(
                str(file),
                select,
                ignore,
                threshold,
                include_file_in_result=True,
                configure=configure,
                config_path=config_path,
            )
            if issues:
                files_with_issues += 1
                all_issues.extend(issues)
                for issue in issues:
                    severity = issue.severity
                    if severity in severity_counts:
                        severity_counts[severity] += 1
        except ToolError:
            # Skip files that fail to parse
            pass

    total_issues = len(all_issues)
    summary = SeveritySummary(E=severity_counts["E"], W=severity_counts["W"], INFO=severity_counts["I"])

    # Calculate top rules for summarize_only mode
    if summarize_only:
        rule_counts: dict[str, int] = {}
        for issue in all_issues:
            rule_id = issue.rule_id
            rule_counts[rule_id] = rule_counts.get(rule_id, 0) + 1
        top_rules = sorted(rule_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_rules_list = [TopRule(rule_id=rule_id, count=count) for rule_id, count in top_rules]

        return LintFilesResult(
            total_files=len(files),
            total_issues=total_issues,
            files_with_issues=files_with_issues,
            summary=summary,
            top_rules=top_rules_list,
            unmatched_patterns=unmatched,
        )

    # Handle grouping vs flat list
    if group_by:
        grouped_issues, group_counts = _group_issues(all_issues, group_by, limit, offset)
        # Check if any group was limited or has more after offset
        limited = limit is not None and any(group_counts[k] > offset + len(v) for k, v in grouped_issues.items())
        has_more = any(group_counts[k] > offset + len(v) for k, v in grouped_issues.items())
        return LintFilesResult(
            total_files=len(files),
            total_issues=total_issues,
            files_with_issues=files_with_issues,
            issues=grouped_issues,
            summary=summary,
            limited=limited,
            offset=offset,
            has_more=has_more,
            unmatched_patterns=unmatched,
            group_counts=group_counts,
        )

    # Flat list mode - apply offset and limit
    # Apply offset first
    offset_issues = all_issues[offset:] if offset > 0 else all_issues
    # Then apply limit
    limited = limit is not None and len(offset_issues) > limit
    has_more = len(offset_issues) > (limit if limit else len(offset_issues))
    if limit is not None:
        offset_issues = offset_issues[:limit]

    return LintFilesResult(
        total_files=len(files),
        total_issues=total_issues,
        files_with_issues=files_with_issues,
        issues=offset_issues,
        summary=summary,
        limited=limited,
        offset=offset,
        has_more=has_more,
        unmatched_patterns=unmatched,
    )


def _format_files_impl(
    file_patterns: list[str],
    base_path: str | None = None,
    select: list[str] | None = None,
    space_count: int | None = None,
    line_length: int | None = None,
    *,
    overwrite: bool = False,
    summarize_only: bool = False,
    config_path: Path | None = None,
) -> FormatFilesResult:
    """
    Format multiple Robot Framework files.

    Args:
        file_patterns: List of file paths or glob patterns.
        base_path: Base directory for resolving relative paths/patterns.
        select: List of formatter names to apply.
        space_count: Number of spaces for indentation.
        line_length: Maximum line length.
        overwrite: Whether to overwrite files with formatted content.
        config_path: Path to the Robocop toml configuration file
        summarize_only: If True, return only summary statistics without per-file results.
            Useful for large codebases to reduce response size.

    Returns:
        A FormatFilesResult model containing the formatting results.
        When summarize_only=True, per-file results are omitted.

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

    results: list[FormatFileInfo] = []
    files_changed = 0
    files_unchanged = 0
    files_written = 0
    errors: list[dict[str, str]] = []

    for file in files:
        try:
            result = _format_file_impl(
                str(file), select, space_count, line_length, overwrite=overwrite, config_path=config_path
            )
            if not summarize_only:
                results.append(
                    FormatFileInfo(
                        file=str(file),
                        changed=result.changed,
                        written=result.written,
                    )
                )
            if result.changed:
                files_changed += 1
                if result.written:
                    files_written += 1
            else:
                files_unchanged += 1
        except ToolError as e:
            errors.append({"file": str(file), "error": str(e)})

    return FormatFilesResult(
        total_files=len(files),
        files_changed=files_changed,
        files_unchanged=files_unchanged,
        files_written=files_written,
        errors=errors,
        unmatched_patterns=unmatched,
        results=results if not summarize_only else None,
    )
