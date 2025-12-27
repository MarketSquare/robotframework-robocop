"""Helper functions for MCP tools - utilities and data conversion."""

from __future__ import annotations

import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.utils.constants import THRESHOLD_MAP, VALID_EXTENSIONS

if TYPE_CHECKING:
    from collections.abc import Generator

    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.rules import Rule, RuleParam, RuleSeverity


def _create_match_snippet(text: str, query: str, context: int = 30) -> str:
    """
    Create a snippet around the first match with surrounding context.

    Args:
        text: The text to search in.
        query: The query string to find.
        context: Number of characters to include before and after the match.

    Returns:
        A snippet with ellipsis if truncated, or empty string if no match.

    """
    match_pos = text.lower().find(query.lower())
    if match_pos == -1:
        return ""
    start = max(0, match_pos - context)
    end = min(len(text), match_pos + len(query) + context)
    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet += "..."
    return snippet


def _iter_unique_rules(
    category: str | None = None,
    severity: str | None = None,
    enabled_only: bool = False,
) -> Generator[Rule, None, None]:
    """
    Yield unique rules with optional filtering.

    Args:
        category: Filter by rule category/group (e.g., "LEN", "NAME", "DOC").
        severity: Filter by severity ("I", "W", or "E").
        enabled_only: If True, only yield enabled rules.

    Yields:
        Rule objects matching the filters.

    """
    from robocop.mcp.cache import get_linter_config

    linter_config = get_linter_config()
    seen_ids: set[str] = set()

    for rule in linter_config.rules.values():
        if rule.rule_id in seen_ids:
            continue
        seen_ids.add(rule.rule_id)

        if enabled_only and not rule.enabled:
            continue
        if category and not rule.rule_id.startswith(category.upper()):
            continue
        if severity and rule.severity.value != severity.upper():
            continue

        yield rule


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
