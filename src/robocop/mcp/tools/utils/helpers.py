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
