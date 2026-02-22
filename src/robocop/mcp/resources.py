"""MCP Resources for Robocop - Read-only context data exposed via MCP."""

from __future__ import annotations

import operator
from typing import TYPE_CHECKING, Any

from fastmcp.exceptions import ResourceError

from robocop.mcp.cache import get_formatter_config, get_linter_config

if TYPE_CHECKING:
    from pathlib import Path

    from fastmcp import FastMCP


def _get_rules_catalog(config_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Get catalog of all available linting rules.

    Args:
        config_path: Path to the Robocop toml configuration file

    Returns:
        list[dict[str, Any]]: List of rules with basic information.

    """
    linter_config = get_linter_config(config_path)

    # Use a set to deduplicate (rules dict has both id and name pointing to same rule)
    seen_ids: set[str] = set()
    rules = []

    for rule in linter_config.rules.values():
        if rule.rule_id in seen_ids:
            continue
        seen_ids.add(rule.rule_id)

        rules.append(
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "message": rule.message,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "deprecated": rule.deprecated,
                "added_in_version": rule.added_in_version,
            }
        )

    return sorted(rules, key=operator.itemgetter("rule_id"))


def _get_formatters_catalog(config_path: Path | None = None) -> list[dict[str, Any]]:
    """
    Get catalog of all available formatters.

    Args:
        config_path: Path to the Robocop toml configuration file

    Returns:
        list[dict[str, Any]]: List of formatters with basic information.

    """
    formatter_config = get_formatter_config(config_path)

    formatters = []
    for name, formatter in formatter_config.formatters.items():
        doc = formatter.__doc__ or ""
        description = doc.strip().split("\n")[0] if doc else "No description"

        formatters.append(
            {
                "name": name,
                "enabled": getattr(formatter, "ENABLED", True),
                "description": description,
            }
        )

    return sorted(formatters, key=operator.itemgetter("name"))


def _get_rule_details(rule_id: str, config_path: Path | None = None) -> dict[str, Any]:
    """
    Get detailed information about a specific rule.

    Args:
        rule_id: Rule ID (e.g., "LEN01") or name (e.g., "too-long-keyword")
        config_path: Path to the Robocop toml configuration file

    Returns:
        dict[str, Any]: Detailed rule information including full documentation
        and configurable parameters.

    """
    linter_config = get_linter_config(config_path)

    if rule_id not in linter_config.rules:
        raise ResourceError(f"Rule '{rule_id}' not found")

    rule = linter_config.rules[rule_id]

    parameters = (
        [
            {
                "name": param.name,
                "default": str(param.raw_value) if param.raw_value is not None else None,
                "description": param.desc,
                "type": param.param_type,
            }
            for param in rule.parameters
        ]
        if rule.parameters
        else []
    )

    return {
        "rule_id": rule.rule_id,
        "name": rule.name,
        "message": rule.message,
        "severity": rule.severity.value,
        "enabled": rule.enabled,
        "deprecated": rule.deprecated,
        "docs": rule.docs,
        "parameters": parameters,
        "added_in_version": rule.added_in_version,
        "version_requirement": rule.version or None,
    }


def register_resources(mcp: FastMCP) -> None:
    """Register all MCP resources with the server."""

    @mcp.resource("robocop://rules")  # FIXME: add config handling
    def get_rules_catalog() -> list[dict[str, Any]]:
        """
        Get catalog of all available linting rules.

        Returns a list of rules with basic information:
        - rule_id: Unique identifier (e.g., "LEN01")
        - name: Human-readable name (e.g., "too-long-keyword")
        - message: Issue message template
        - severity: Default severity (I/W/E)
        - enabled: Whether enabled by default
        - deprecated: Whether the rule is deprecated
        - added_in_version: Robocop version when added

        Returns:
            list[dict]: List of rules with basic information.

        """
        return _get_rules_catalog()

    @mcp.resource("robocop://formatters")
    def get_formatters_catalog() -> list[dict[str, Any]]:
        """
        Get catalog of all available formatters.

        Returns a list of formatters with:
        - name: Formatter name
        - enabled: Whether enabled by default
        - description: Brief description

        Returns:
            list[dict]: List of formatters with basic information.

        """
        return _get_formatters_catalog()

    @mcp.resource("robocop://rules/{rule_id}")
    def get_rule_details(rule_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific rule.

        Args:
            rule_id: Rule ID (e.g., "LEN01") or name (e.g., "too-long-keyword")

        Returns:
            detailed rule information including full documentation
            and configurable parameters.

        """
        return _get_rule_details(rule_id)
