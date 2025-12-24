"""MCP Tools for Robocop - Linting and formatting tools exposed via MCP."""

from __future__ import annotations

import inspect
import operator
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
    configure: list[str] | None = None,
) -> LinterConfig:
    """Create a LinterConfig with the given options."""
    return LinterConfig(
        select=select or [],
        ignore=ignore or [],
        configure=configure or [],
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
    configure: list[str] | None = None,
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
        configure: A list of rule configurations (e.g., ["rule-name.param=value"]).

    Returns:
        A list of dictionaries representing the diagnostics.

    Raises:
        ToolError: If the content cannot be parsed.

    """
    from robocop.linter.runner import RobocopLinter

    suffix = _normalize_suffix(filename)

    with _temp_robot_file(content, suffix) as tmp_path:
        try:
            linter_config = _create_linter_config(select, ignore, threshold, configure)
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
    configure: list[str] | None = None,
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
        configure: A list of rule configurations (e.g., ["rule-name.param=value"]).

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
        linter_config = _create_linter_config(select, ignore, threshold, configure)
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


# Characters that indicate a glob pattern
GLOB_CHARS = frozenset("*?[]")


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


# Valid group_by options for batch linting
VALID_GROUP_BY = frozenset(("severity", "rule", "file"))


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


def _list_rules_impl(
    category: str | None = None,
    severity: str | None = None,
    enabled_only: bool = False,
) -> list[dict[str, Any]]:
    """
    List all available linting rules with optional filtering.

    Args:
        category: Filter by rule category/group (e.g., "LEN", "NAME", "DOC")
        severity: Filter by severity ("I", "W", or "E")
        enabled_only: If True, only return enabled rules

    Returns:
        A list of rule summary dictionaries.

    """
    from robocop.mcp.cache import get_linter_config

    linter_config = get_linter_config()

    # Get unique rules (avoid duplicates from name/id mapping)
    seen_ids = set()
    rules = []
    for rule in linter_config.rules.values():
        if rule.rule_id in seen_ids:
            continue
        seen_ids.add(rule.rule_id)

        # Apply filters
        if enabled_only and not rule.enabled:
            continue
        if category and not rule.rule_id.startswith(category.upper()):
            continue
        if severity and rule.severity.value != severity.upper():
            continue

        rules.append(
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "message": rule.message,
            }
        )

    return sorted(rules, key=operator.itemgetter("rule_id"))


def _list_formatters_impl(enabled_only: bool = True) -> list[dict[str, Any]]:
    """
    List all available formatters.

    Args:
        enabled_only: If True, only return enabled formatters (default: True)

    Returns:
        A list of formatter summary dictionaries.

    """
    from robocop.mcp.cache import get_formatter_config

    formatter_config = get_formatter_config()
    formatters = formatter_config.formatters

    result = []
    for name, formatter in formatters.items():
        formatter_class = formatter.__class__
        is_enabled = getattr(formatter_class, "ENABLED", True)

        if enabled_only and not is_enabled:
            continue

        result.append(
            {
                "name": name,
                "enabled": is_enabled,
                "description": (formatter.__doc__ or "No description.").split("\n")[0].strip(),
            }
        )

    return sorted(result, key=operator.itemgetter("name"))


def _suggest_fixes_impl(
    content: str,
    filename: str = "stdin.robot",
    rule_ids: list[str] | None = None,
) -> dict[str, Any]:
    """
    Suggest fixes for linting issues in Robot Framework code.

    Args:
        content: The Robot Framework source code to analyze.
        filename: The virtual filename (affects parsing).
        rule_ids: Optional list of rule IDs to get suggestions for.

    Returns:
        A dictionary containing fix suggestions.

    """
    from robocop.mcp.cache import get_linter_config

    # Get lint issues first
    issues = _lint_content_impl(content, filename, select=rule_ids)

    # Get rule objects to look up fix_suggestion attribute
    linter_config = get_linter_config()
    rules = linter_config.rules

    fixes = []
    auto_fixable = 0
    manual_required = 0

    for issue in issues:
        rule_id = issue["rule_id"]
        category = rule_id[:3] if len(rule_id) >= 3 else rule_id

        # Get suggestion from rule's fix_suggestion attribute, or provide a generic one
        suggestion = None
        if rule_id in rules and rules[rule_id].fix_suggestion:
            suggestion = rules[rule_id].fix_suggestion
        else:
            suggestion = f"Review the rule documentation for {rule_id} ({issue['name']})."

        # Determine if auto-fixable (formatting issues generally are)
        is_auto_fixable = category in {"SPACE", "MISC"} or rule_id == "LEN08"

        if is_auto_fixable:
            auto_fixable += 1
        else:
            manual_required += 1

        fixes.append(
            {
                "rule_id": rule_id,
                "name": issue["name"],
                "line": issue["line"],
                "message": issue["message"],
                "suggestion": suggestion,
                "auto_fixable": is_auto_fixable,
            }
        )

    return {
        "fixes": fixes,
        "total_issues": len(fixes),
        "auto_fixable": auto_fixable,
        "manual_required": manual_required,
        "recommendation": (
            "Run format_content to apply automatic fixes, then address manual fixes."
            if auto_fixable > 0
            else "All issues require manual fixes."
        ),
    }


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


def _get_formatter_parameters(formatter_class: type) -> list[dict[str, Any]]:
    """
    Extract configurable parameters from a formatter class's __init__ signature.

    Args:
        formatter_class: The formatter class to extract parameters from.

    Returns:
        A list of parameter dictionaries with name, default, and type.

    """
    try:
        spec = inspect.getfullargspec(formatter_class.__init__)
    except TypeError:
        return []

    params = []
    args = spec.args[1:]  # Skip 'self'
    defaults = spec.defaults or ()
    annotations = spec.annotations or {}

    # Calculate where defaults start
    defaults_start = len(args) - len(defaults)

    for i, arg in enumerate(args):
        # Skip the 'skip' parameter as it's internal
        if arg == "skip":
            continue

        default = None
        if i >= defaults_start:
            default = defaults[i - defaults_start]

        # Get type from annotation or infer from default
        param_type = "str"
        if arg in annotations:
            type_hint = annotations[arg]
            if hasattr(type_hint, "__name__"):
                param_type = type_hint.__name__
            elif hasattr(type_hint, "_name"):
                param_type = getattr(type_hint, "_name", None) or "str"
        elif default is not None:
            param_type = type(default).__name__

        params.append(
            {
                "name": arg,
                "default": default,
                "type": param_type,
            }
        )

    return params


def _get_formatter_info_impl(formatter_name: str) -> dict[str, Any]:
    """
    Look up formatter information by name.

    Args:
        formatter_name: Formatter name (e.g., "NormalizeSeparators", "AlignKeywordsSection")

    Returns:
        Dictionary containing:
        - name: Formatter name
        - enabled: Whether enabled by default
        - docs: Full documentation
        - min_version: Minimum Robot Framework version (if any)
        - parameters: List of configurable parameters
        - skip_options: List of skip options the formatter handles

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
    formatter_class = formatter.__class__

    # Get skip options handled by this formatter
    handles_skip = getattr(formatter_class, "HANDLES_SKIP", frozenset())

    return {
        "name": formatter_name,
        "enabled": getattr(formatter_class, "ENABLED", True),
        "docs": formatter.__doc__ or "No documentation available.",
        "min_version": getattr(formatter_class, "MIN_VERSION", None),
        "parameters": _get_formatter_parameters(formatter_class),
        "skip_options": sorted(handles_skip) if handles_skip else [],
    }


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

        base = Path(base_path) if base_path else None
        files, unmatched = _expand_file_patterns(file_patterns, base)

        if ctx:
            if unmatched:
                await ctx.warning(f"Patterns with no matches: {unmatched}")
            await ctx.info(f"Found {len(files)} Robot Framework file(s) to lint")

        if not files:
            raise ToolError(
                f"No .robot or .resource files found matching patterns: {file_patterns}"
                + (f" (unmatched: {unmatched})" if unmatched else "")
            )

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
                "unmatched_patterns": unmatched,
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
            "unmatched_patterns": unmatched,
        }

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
