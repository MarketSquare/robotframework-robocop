"""Documentation and discovery functionality for MCP tools."""

from __future__ import annotations

import inspect
import operator
from typing import TYPE_CHECKING

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.models import (
    FormatterDetail,
    FormatterParam,
    FormatterSummary,
    PromptArgument,
    PromptSummary,
    RuleDetail,
    RuleSearchResult,
    RuleSummary,
)
from robocop.mcp.tools.utils.helpers import (
    _create_match_snippet,
    _iter_unique_rules,
    _rule_to_dict,
)

if TYPE_CHECKING:
    from pathlib import Path

    from fastmcp import FastMCP

    from robocop.formatter.formatters import Formatter


def _list_rules_impl(
    category: str | None = None,
    severity: str | None = None,
    enabled_only: bool = False,
    config_path: Path | None = None,
) -> list[RuleSummary]:
    """
    List all available linting rules with optional filtering.

    Args:
        category: Filter by rule category/group (e.g., "LEN", "NAME", "DOC")
        severity: Filter by severity ("I", "W", or "E")
        enabled_only: If True, only return enabled rules
        config_path: Path to the Robocop toml configuration file

    Returns:
        A list of RuleSummary models.

    """
    rules = [
        RuleSummary(
            rule_id=rule.rule_id,
            name=rule.name,
            severity=rule.severity.value,
            enabled=rule.enabled,
            message=rule.message,
        )
        for rule in _iter_unique_rules(category, severity, enabled_only, config_path)
    ]
    return sorted(rules, key=operator.attrgetter("rule_id"))


def _list_formatters_impl(enabled_only: bool = True, config_path: Path | None = None) -> list[FormatterSummary]:
    """
    List all available formatters.

    Args:
        enabled_only: If True, only return enabled formatters (default: True)
        config_path: Path to the Robocop toml configuration file

    Returns:
        A list of FormatterSummary models.

    """
    from robocop.mcp.cache import get_formatter_config

    formatter_config = get_formatter_config(config_path)
    formatters = formatter_config.formatters

    result: list[FormatterSummary] = []
    for name, formatter in formatters.items():
        formatter_class = formatter.__class__
        is_enabled = getattr(formatter_class, "ENABLED", True)

        if enabled_only and not is_enabled:
            continue

        result.append(
            FormatterSummary(
                name=name,
                enabled=is_enabled,
                description=(formatter.__doc__ or "No description.").split("\n")[0].strip(),
            )
        )

    return sorted(result, key=lambda f: f.name)


def _get_formatter_parameters(formatter_class: type[Formatter]) -> list[FormatterParam]:
    """
    Extract configurable parameters from a formatter class's __init__ signature.

    Args:
        formatter_class: The formatter class to extract parameters from.

    Returns:
        A list of FormatterParam models with name, default, and type.

    """
    try:
        spec = inspect.getfullargspec(formatter_class.__init__)
    except TypeError:
        return []

    params: list[FormatterParam] = []
    args = spec.args[1:]  # Skip 'self'
    defaults = spec.defaults or ()
    annotations = spec.annotations or {}

    # Calculate where defaults start
    defaults_start = len(args) - len(defaults)

    for i, arg in enumerate(args):
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
            else:
                param_type = type_hint
        elif default is not None:
            param_type = type(default).__name__

        params.append(
            FormatterParam(
                name=arg,
                default=default,
                type=param_type,
            )
        )

    return params


def _get_rule_info_impl(rule_name_or_id: str, config_path: Path | None = None) -> RuleDetail:
    """
    Look up rule information by name or ID.

    Args:
        rule_name_or_id: Rule name (e.g., "too-long-keyword") or ID (e.g., "LEN01")
        config_path: Path to the Robocop toml configuration file

    Returns:
        A RuleDetail model containing:
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

    linter_config = get_linter_config(config_path)

    if rule_name_or_id not in linter_config.rules:
        available = ", ".join(sorted({r.rule_id for r in linter_config.rules.values()}))
        raise ToolError(
            f"Rule '{rule_name_or_id}' not found. "
            f"Use rule ID (e.g., 'LEN01') or name (e.g., 'too-long-keyword'). "
            f"Available rule IDs: {available[:200]}..."
        )

    return _rule_to_dict(linter_config.rules[rule_name_or_id])


def _search_rules_impl(
    query: str,
    fields: list[str] | None = None,
    category: str | None = None,
    severity: str | None = None,
    limit: int = 20,
    config_path: Path | None = None,
) -> list[RuleSearchResult]:
    """
    Search rules by keyword across specified fields.

    Args:
        query: The search query (case-insensitive substring match).
        fields: Fields to search in. Defaults to ["name", "message", "docs"].
            Valid fields: "name", "message", "docs", "rule_id".
        category: Optional filter by rule category (e.g., "LEN", "NAME").
        severity: Optional filter by severity ("I", "W", "E").
        limit: Maximum number of results to return (default: 20).
        config_path: Path to the Robocop toml configuration file

    Returns:
        A list of RuleSearchResult models with rule_id, name, message, severity,
        match_field (which field matched), and match_snippet (context around match).

    """
    if fields is None:
        fields = ["name", "message", "docs"]

    query_lower = query.lower()
    results: list[RuleSearchResult] = []

    for rule in _iter_unique_rules(category, severity, config_path=config_path):
        for field in fields:
            field_value = getattr(rule, field, "") or ""
            if query_lower in field_value.lower():
                results.append(
                    RuleSearchResult(
                        rule_id=rule.rule_id,
                        name=rule.name,
                        message=rule.message,
                        severity=rule.severity.value,
                        enabled=rule.enabled,
                        match_field=field,
                        match_snippet=_create_match_snippet(field_value, query),
                    )
                )
                break  # Only match once per rule

        if len(results) >= limit:
            break

    return results


def _list_prompts_impl(mcp: FastMCP) -> list[PromptSummary]:
    """
    List all available MCP prompt templates.

    Returns:
        A list of PromptSummary models with name, description, and arguments.

    """
    prompts = [
        PromptSummary(
            name=prompt.name,
            description=prompt.description or "",
            arguments=[PromptArgument(name=arg.name, required=arg.required) for arg in prompt.arguments]
            if prompt.arguments
            else [],
        )
        for prompt in mcp._prompt_manager._prompts.values()  # noqa: SLF001
    ]
    return sorted(prompts, key=lambda p: p.name)


def _get_formatter_info_impl(formatter_name: str, config_path: Path | None = None) -> FormatterDetail:
    """
    Look up formatter information by name.

    Args:
        formatter_name: Formatter name (e.g., "NormalizeSeparators", "AlignKeywordsSection")
        config_path: Path to the Robocop toml configuration file

    Returns:
        A FormatterDetail model containing:
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

    formatter_config = get_formatter_config(config_path)
    formatters = formatter_config.formatters

    if formatter_name not in formatters:
        available = ", ".join(sorted(formatters.keys()))
        raise ToolError(f"Formatter '{formatter_name}' not found. Available formatters: {available}")

    formatter = formatters[formatter_name]
    formatter_class = formatter.__class__

    # Get skip options handled by this formatter
    handles_skip: frozenset[str] = getattr(formatter_class, "HANDLES_SKIP", frozenset())

    return FormatterDetail(
        name=formatter_name,
        enabled=getattr(formatter_class, "ENABLED", True),
        docs=formatter.__doc__ or "No documentation available.",
        min_version=getattr(formatter_class, "MIN_VERSION", None),
        parameters=_get_formatter_parameters(formatter_class),
        skip_options=sorted(handles_skip) if handles_skip else [],
    )
