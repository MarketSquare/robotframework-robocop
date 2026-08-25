"""Module containing helper methods for listing the rules."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from rich.text import Text

from robocop.linter.fix import FixAvailability

if TYPE_CHECKING:
    from re import Pattern

    from robocop.linter.rules import Rule
    from robocop.version_handling import Version


class RuleFilter(str, Enum):
    ALL = "ALL"
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    DEPRECATED = "DEPRECATED"
    STYLE_GUIDE = "STYLE_GUIDE"
    PROJECT = "PROJECT"


def rules_sorted_by_id(rules: dict[str, Rule]) -> list[Rule]:
    """Return rules list from rules dictionary sorted by rule id."""
    return sorted(rules.values(), key=lambda x: x.rule_id)


def filter_rules_by_pattern(rules: dict[str, Rule], pattern: Pattern[str]) -> list[Rule]:
    """Return a sorted list of Rules from the rules dictionary, filtered out by pattern."""

    def matches_pattern(rule: Rule, pattern: str | Pattern[str]) -> bool:
        if isinstance(pattern, str):
            return pattern in (rule.name, rule.rule_id)
        return bool(pattern.match(rule.name) or pattern.match(rule.rule_id))

    return rules_sorted_by_id(
        {rule.rule_id: rule for rule in rules.values() if matches_pattern(rule, pattern) and not rule.deprecated}
    )


def filter_rules_by_category(rules: dict[str, Rule], category: RuleFilter, target_version: Version) -> list[Rule]:
    """Return a sorted list of Rules from the rules dictionary, filtered by rule category."""
    if category == RuleFilter.ALL:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated}
    elif category == RuleFilter.ENABLED:
        rules_by_id = {
            rule.rule_id: rule for rule in rules.values() if rule.enabled and not rule.is_disabled(target_version)
        }
    elif category == RuleFilter.DISABLED:
        rules_by_id = {
            rule.rule_id: rule
            for rule in rules.values()
            if not rule.deprecated and (not rule.enabled or rule.is_disabled(target_version))
        }
    elif category == RuleFilter.DEPRECATED:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if rule.deprecated}
    elif category == RuleFilter.STYLE_GUIDE:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated and rule.style_guide_ref}
    elif category == RuleFilter.PROJECT:
        rules_by_id = {rule.rule_id: rule for rule in rules.values() if not rule.deprecated and rule.project_rule}
    else:
        raise ValueError(f"Unrecognized rule category '{category}'")
    return rules_sorted_by_id(rules_by_id)


def filter_rules_by_fixability(rules: list[Rule]) -> list[Rule]:
    return [rule for rule in rules if rule.fix_availability in (FixAvailability.ALWAYS, FixAvailability.SOMETIMES)]


def rule_short_description(rule: Rule, target_version: Version) -> Text:
    desc = Text(f"{rule.rule_id} [{rule.severity}]: {rule.name}: {rule.message} (")
    if rule.deprecated:
        desc.append("deprecated", style="yellow")
    elif rule.version and not rule.supported_in_target_version(target_version):
        desc.append("disabled", style="red")
        desc.append(f" - supported only for RF version {rule.version}")
    elif rule.enabled:
        desc.append("enabled", style="green")
        if rule.default_enabled != rule.enabled:
            desc.append("*", style="cyan")
    else:
        desc.append("disabled", style="red")
        if rule.default_enabled != rule.enabled:
            desc.append("*", style="cyan")
    desc.append(")")
    if rule.fix_availability in (FixAvailability.ALWAYS, FixAvailability.SOMETIMES):
        desc.append(" [fixable]", style="blue")
    if rule.project_rule:
        desc.append(" [project]", style="magenta")
    return desc
