"""Documentation and discovery functionality for MCP tools."""

from __future__ import annotations

import inspect
import operator
from typing import Any

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.utils.helpers import _create_match_snippet, _iter_unique_rules, _rule_to_dict


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
    rules = [
        {
            "rule_id": rule.rule_id,
            "name": rule.name,
            "severity": rule.severity.value,
            "enabled": rule.enabled,
            "message": rule.message,
        }
        for rule in _iter_unique_rules(category, severity, enabled_only)
    ]
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


def _search_rules_impl(
    query: str,
    fields: list[str] | None = None,
    category: str | None = None,
    severity: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    Search rules by keyword across specified fields.

    Args:
        query: The search query (case-insensitive substring match).
        fields: Fields to search in. Defaults to ["name", "message", "docs"].
            Valid fields: "name", "message", "docs", "rule_id".
        category: Optional filter by rule category (e.g., "LEN", "NAME").
        severity: Optional filter by severity ("I", "W", "E").
        limit: Maximum number of results to return (default: 20).

    Returns:
        A list of matching rules with rule_id, name, message, severity,
        match_field (which field matched), and match_snippet (context around match).

    """
    if fields is None:
        fields = ["name", "message", "docs"]

    query_lower = query.lower()
    results: list[dict[str, Any]] = []

    for rule in _iter_unique_rules(category, severity):
        for field in fields:
            field_value = getattr(rule, field, "") or ""
            if query_lower in field_value.lower():
                results.append(
                    {
                        "rule_id": rule.rule_id,
                        "name": rule.name,
                        "message": rule.message,
                        "severity": rule.severity.value,
                        "enabled": rule.enabled,
                        "match_field": field,
                        "match_snippet": _create_match_snippet(field_value, query),
                    }
                )
                break  # Only match once per rule

        if len(results) >= limit:
            break

    return results


def _is_mcp_prompt_decorator(decorator: Any) -> bool:
    import ast

    if not isinstance(decorator, ast.Call):
        return False
    return hasattr(decorator.func, "attr") and decorator.func.attr == "prompt"


def _extract_prompt_info(func_node: Any) -> dict[str, Any]:
    import ast

    # Get docstring - first line only
    docstring = ast.get_docstring(func_node) or ""
    description = docstring.split("\n")[0].strip()

    # Get arguments and their defaults
    args = func_node.args
    num_defaults = len(args.defaults)
    num_args = len(args.args)

    arguments = []
    for i, arg in enumerate(args.args):
        # Arguments with defaults are at the end
        has_default = i >= (num_args - num_defaults)
        arguments.append({"name": arg.arg, "required": not has_default})

    return {
        "name": func_node.name,
        "description": description,
        "arguments": arguments,
    }


def _list_prompts_impl() -> list[dict[str, Any]]:
    """
    List all available MCP prompt templates.

    Introspects the prompts module using AST to extract prompt definitions
    without requiring async execution.

    Returns:
        A list of prompt dictionaries with name, description, and arguments.

    """
    import ast

    from robocop.mcp import prompts

    source = inspect.getsource(prompts)
    tree = ast.parse(source)

    results: list[dict[str, Any]] = []

    # Find the register_prompts function
    register_func = next(
        (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "register_prompts"),
        None,
    )
    if register_func is None:
        return results

    # Find decorated functions inside register_prompts
    for child in ast.walk(register_func):
        if not isinstance(child, ast.FunctionDef) or child.name == "register_prompts":
            continue

        # Check if decorated with @mcp.prompt()
        if any(_is_mcp_prompt_decorator(d) for d in child.decorator_list):
            results.append(_extract_prompt_info(child))

    return sorted(results, key=operator.itemgetter("name"))


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
