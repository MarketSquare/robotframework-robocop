"""Helper functions for MCP tools - utilities and data conversion."""

from __future__ import annotations

import operator
import tempfile
import types
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypedDict, Union, get_args, get_origin

from fastmcp.exceptions import ToolError

from robocop.mcp.tools.models import DiagnosticResult, RuleDetail
from robocop.mcp.tools.models import RuleParam as RuleParamModel
from robocop.mcp.tools.utils.constants import (
    CONFIG_SECTIONS,
    THRESHOLD_MAP,
    VALID_EXTENSIONS,
)

# --- Type Definitions for Catalog Structures ---


class RuleParamInfo(TypedDict):
    """Parameter information for a rule in the catalog."""

    name: str
    type: str
    default: str
    description: str


class RuleCatalogEntry(TypedDict):
    """Entry in the rule catalog returned by build_rule_catalog()."""

    rule_id: str
    name: str
    description: str
    severity: str
    enabled: bool
    deprecated: bool
    parameters: list[RuleParamInfo]


class ConfigOptionInfo(TypedDict):
    """Configuration option information for the config catalog."""

    name: str
    type: str
    default: str


class SuggestionDict(TypedDict, total=False):
    """
    Suggestion dict used for conflict detection and TOML generation.

    All fields are optional since different actions require different fields.
    """

    rule_id: str
    rule_name: str
    action: str
    parameter: str
    value: str
    section: str


# Type alias for the config options catalog
ConfigOptionsCatalog = dict[str, list[ConfigOptionInfo]]

if TYPE_CHECKING:
    from collections.abc import Generator
    from dataclasses import Field

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
    with tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False, encoding="utf-8") as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    try:
        yield tmp_path
    finally:
        tmp_path.unlink(missing_ok=True)


def _diagnostic_to_dict(diagnostic: Diagnostic, file_path: str | None = None) -> DiagnosticResult:
    """
    Convert a Diagnostic object to a DiagnosticResult model.

    Args:
        diagnostic: The Diagnostic object to convert.
        file_path: Optional file path to include in the result.

    Returns:
        A DiagnosticResult Pydantic model.

    """
    return DiagnosticResult(
        rule_id=diagnostic.rule.rule_id,
        name=diagnostic.rule.name,
        message=diagnostic.message,
        severity=diagnostic.severity.value,
        line=diagnostic.range.start.line,
        column=diagnostic.range.start.character,
        end_line=diagnostic.range.end.line,
        end_column=diagnostic.range.end.character,
        file=file_path,
    )


def _param_to_dict(param: RuleParam) -> RuleParamModel:
    """
    Convert a RuleParam to a RuleParamModel.

    Args:
        param: The RuleParam to convert.

    Returns:
        A RuleParamModel Pydantic model.

    """
    return RuleParamModel(
        name=param.name,
        default=str(param.raw_value) if param.raw_value is not None else None,
        description=param.desc,
        type=param.param_type,
    )


def _rule_to_dict(rule: Rule) -> RuleDetail:
    """
    Convert a Rule to a RuleDetail model.

    Args:
        rule: The Rule to convert.

    Returns:
        A RuleDetail Pydantic model.

    """
    return RuleDetail(
        rule_id=rule.rule_id,
        name=rule.name,
        message=rule.message,
        severity=rule.severity.value,
        enabled=rule.enabled,
        deprecated=rule.deprecated,
        docs=rule.docs,
        parameters=([_param_to_dict(p) for p in rule.parameters] if rule.parameters else []),
        added_in_version=rule.added_in_version,
        version_requirement=rule.version or None,
    )


# --- Natural Language Configuration Helpers ---


@dataclass
class _RuleLookupCache:
    """Lazy-initialized cache for O(1) rule lookups by ID or name."""

    _by_id: dict[str, Rule] | None = field(default=None, init=False)
    _by_name: dict[str, Rule] | None = field(default=None, init=False)

    def _ensure_populated(self) -> None:
        """Populate the lookup tables on first access."""
        if self._by_id is not None:
            return

        from robocop.mcp.cache import get_linter_config

        linter_config = get_linter_config()
        self._by_id = {}
        self._by_name = {}

        for rule in linter_config.rules.values():
            # Store by uppercase ID and lowercase name for case-insensitive lookup
            self._by_id[rule.rule_id.upper()] = rule
            self._by_name[rule.name.lower()] = rule

    def get(self, identifier: str) -> Rule | None:
        """
        Find a rule by its name or ID.

        Args:
            identifier: The rule name or ID (case-insensitive).

        Returns:
            The Rule object if found, None otherwise.

        """
        self._ensure_populated()
        assert self._by_id is not None
        assert self._by_name is not None

        # Try ID lookup first (uppercase), then name lookup (lowercase)
        return self._by_id.get(identifier.upper()) or self._by_name.get(identifier.lower())


# Module-level cache instance
_rule_cache = _RuleLookupCache()


def get_rule_by_name_or_id(identifier: str) -> Rule | None:
    """
    Find a rule by its name or ID (cached O(1) lookup).

    Args:
        identifier: The rule name (e.g., "line-too-long") or ID (e.g., "LEN02").

    Returns:
        The Rule object if found, None otherwise.

    """
    return _rule_cache.get(identifier)


def validate_rule_param(rule_name: str, param_name: str, value: str) -> tuple[bool, str | None, str | None]:
    """
    Validate and convert a parameter value for a rule.

    Args:
        rule_name: The rule name or ID.
        param_name: The parameter name to configure.
        value: The string value to validate and convert.

    Returns:
        A tuple of (is_valid, converted_value_str, error_message).
        - is_valid: True if the value is valid for this parameter.
        - converted_value_str: The validated value as a string, or None if invalid.
        - error_message: An error message if invalid, None otherwise.

    """
    rule = get_rule_by_name_or_id(rule_name)
    if rule is None:
        return False, None, f"Rule '{rule_name}' not found"

    # Find the parameter in the rule's config
    if param_name not in rule.config:
        available_params = [p for p in rule.config if p != "severity"]
        return (
            False,
            None,
            f"Parameter '{param_name}' not found for rule '{rule.name}'. Available: {available_params}",
        )

    param = rule.config[param_name]

    try:
        # Use the parameter's converter to validate the value
        param.converter(value)
        # Return the string representation of the converted value
        return True, str(value), None
    except (ValueError, TypeError) as e:
        return False, None, f"Invalid value '{value}' for parameter '{param_name}': {e}"
    except Exception as e:  # noqa: BLE001 - converter may raise any exception
        return (
            False,
            None,
            f"Error converting value '{value}' for parameter '{param_name}': {e}",
        )


def detect_config_conflicts(suggestions: list[SuggestionDict]) -> list[str]:
    """
    Detect conflicts in configuration suggestions.

    Conflicts include:
    - Enabling and disabling the same rule
    - Configuring a parameter on a disabled rule

    Args:
        suggestions: List of suggestion dicts with action, rule_id, rule_name, etc.

    Returns:
        List of warning messages for detected conflicts.

    """
    warnings = []

    enabled_rules: set[str] = set()
    disabled_rules: set[str] = set()
    configured_rules: set[str] = set()

    for suggestion in suggestions:
        rule_id = suggestion.get("rule_id", "")
        action = suggestion.get("action", "")

        if action == "enable":
            enabled_rules.add(rule_id)
        elif action == "disable":
            disabled_rules.add(rule_id)
        elif action == "configure":
            configured_rules.add(rule_id)

    # Check for enable/disable conflicts
    conflicts = enabled_rules & disabled_rules
    for rule_id in conflicts:
        warnings.append(f"Conflict: Rule '{rule_id}' is both enabled and disabled in the same configuration")

    # Check for configuring disabled rules (just a warning, still valid)
    configured_disabled = configured_rules & disabled_rules
    for rule_id in configured_disabled:
        warnings.append(f"Warning: Rule '{rule_id}' is configured but also disabled")

    return warnings


@cache
def build_rule_catalog() -> list[RuleCatalogEntry]:
    """
    Build a catalog of all rules with moderate detail for LLM context.

    Results are cached since rules don't change during a session.

    Returns:
        List of rule dictionaries with:
        - rule_id: The rule ID (e.g., "LEN02")
        - name: The rule name (e.g., "line-too-long")
        - description: One-sentence description
        - severity: Default severity ("I", "W", or "E")
        - enabled: Whether enabled by default
        - deprecated: Whether the rule is deprecated
        - parameters: List of parameter dicts with name, type, default, description

    """
    from robocop.mcp.cache import get_linter_config

    linter_config = get_linter_config()
    seen_ids: set[str] = set()
    catalog = []

    for rule in linter_config.rules.values():
        if rule.rule_id in seen_ids:
            continue
        seen_ids.add(rule.rule_id)

        # Extract first sentence of docs as description
        description = ""
        if rule.docs:
            first_line = rule.docs.strip().split("\n")[0].strip()
            description = first_line[:200] if len(first_line) > 200 else first_line

        # Build parameter list (exclude 'severity' which all rules have)
        params = []
        if rule.parameters:
            for param in rule.parameters:
                params.append(
                    {
                        "name": param.name,
                        "type": param.param_type,
                        "default": (str(param.raw_value) if param.raw_value is not None else ""),
                        "description": param.desc or "",
                    }
                )

        catalog.append(
            {
                "rule_id": rule.rule_id,
                "name": rule.name,
                "description": description,
                "severity": rule.severity.value,
                "enabled": rule.enabled,
                "deprecated": rule.deprecated,
                "parameters": params,
            }
        )

    # Sort by rule_id for consistent output
    catalog.sort(key=operator.itemgetter("rule_id"))
    return catalog


@cache
def build_config_options_catalog() -> ConfigOptionsCatalog:
    """
    Build a catalog of all configuration options by introspecting Robocop's dataclasses.

    Dynamically extracts config options from Config, LinterConfig, FormatterConfig,
    and related classes so that new options are automatically discovered.

    Results are cached since config options don't change during a session.

    Returns:
        Dict with keys 'common', 'lint', 'format', each containing a list of option dicts.
        Each option dict has: name, type, default, description (if available).

    """
    from dataclasses import MISSING, fields

    from robocop.config import (
        CacheConfig,
        Config,
        FileFiltersOptions,
        FormatterConfig,
        LinterConfig,
        WhitespaceConfig,
    )

    catalog: ConfigOptionsCatalog = {
        "common": [],  # [tool.robocop]
        "lint": [],  # [tool.robocop.lint]
        "format": [],  # [tool.robocop.format]
    }

    def get_default_str(f: Field[Any]) -> str:
        """
        Extract default value as string from a dataclass field.

        Args:
            f: The dataclass field.

        Returns:
            The default value as a string, or indication if required.

        """
        if f.default is not MISSING:
            return str(f.default)
        if f.default_factory is not MISSING:
            try:
                val = f.default_factory()
                if isinstance(val, set):
                    return str(list(val)[:3]) + "..." if len(val) > 3 else str(list(val))
                return str(val)
            except (TypeError, ValueError):
                return "(factory)"
        return "(required)"

    def get_type_str(type_hint: Any) -> str:
        """
        Convert type hint to readable string using typing introspection.

        Args:
            type_hint: The type hint to convert.

        Returns:
            Readable string representation of the type hint.

        """
        origin = get_origin(type_hint)
        args = get_args(type_hint)

        # Handle Union types (including X | None from PEP 604)
        if origin is Union or isinstance(type_hint, types.UnionType):
            non_none = [a for a in args if a is not type(None)]
            # Optional[X] shown as "X?"
            if len(non_none) == 1 and type(None) in args:
                return f"{get_type_str(non_none[0])}?"
            return " | ".join(get_type_str(a) for a in args)

        # Handle generic types like list[str], dict[str, int]
        if origin is not None:
            origin_name = getattr(origin, "__name__", str(origin))
            if args:
                args_str = ", ".join(get_type_str(a) for a in args)
                return f"{origin_name}[{args_str}]"
            return origin_name

        # Simple type with __name__ (int, str, bool, etc.)
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__

        # Fallback to string representation
        return str(type_hint).replace("typing.", "").replace("<class '", "").replace("'>", "")

    # Fields to exclude from each class (internal/nested/non-configurable)
    exclude_fields = {
        Config: {
            "linter",
            "formatter",
            "file_filters",
            "cache",
            "languages",
            "sources",
            "config_source",
        },
        LinterConfig: {
            "rules",
            "checkers",
            "config_source",
            "include_rules",
            "include_rules_patterns",
            "exclude_rules",
            "exclude_rules_patterns",
        },
        FormatterConfig: {
            "whitespace_config",
            "skip_config",
            "formatters",
        },
        FileFiltersOptions: set(),
        CacheConfig: set(),
        WhitespaceConfig: set(),
    }

    # Map classes to their config sections
    section_classes: dict[str, list[type]] = {
        "common": [Config, FileFiltersOptions, CacheConfig],
        "lint": [LinterConfig],
        "format": [FormatterConfig, WhitespaceConfig],
    }

    for section, classes in section_classes.items():
        for cls in classes:
            excludes = exclude_fields.get(cls, set())
            for f in fields(cls):
                # Skip internal fields
                if f.name.startswith("_"):
                    continue
                # Skip excluded fields
                if f.name in excludes:
                    continue
                # Skip fields with compare=False (typically internal)
                if not f.compare:
                    continue

                catalog[section].append(
                    {
                        "name": f.name,
                        "type": get_type_str(f.type),
                        "default": get_default_str(f),
                    }
                )

    return catalog


def generate_toml_config_from_suggestions(
    suggestions: list[SuggestionDict],
) -> dict[str, dict[str, Any]]:
    """
    Generate TOML configuration dicts from suggestions for all sections.

    Args:
        suggestions: List of suggestion dicts with keys:
            - action: "configure", "enable", "disable", or "set"
            - section: "common", "lint", or "format"
            - rule_id, rule_name: For rule-related actions
            - parameter, value: For configure/set actions

    Returns:
        Dict with keys 'common', 'lint', 'format', each containing config for that section.

    """
    config: dict[str, dict[str, Any]] = {
        "common": {},  # [tool.robocop]
        "lint": {},  # [tool.robocop.lint]
        "format": {},  # [tool.robocop.format]
    }

    # Track list-based entries per section
    configure_entries: dict[str, list[str]] = {"common": [], "lint": [], "format": []}
    select_entries: dict[str, list[str]] = {"common": [], "lint": [], "format": []}
    ignore_entries: dict[str, list[str]] = {"common": [], "lint": [], "format": []}

    for suggestion in suggestions:
        action = suggestion.get("action", "")
        section = suggestion.get("section", "lint")
        rule_name = suggestion.get("rule_name", "")
        rule_id = suggestion.get("rule_id", "")
        parameter = suggestion.get("parameter", "")
        value = suggestion.get("value", "")

        if action == "configure" and parameter and value:
            # Rule parameter configuration: rule.param=value
            configure_entries[section].append(f"{rule_name}.{parameter}={value}")
        elif action == "enable" and rule_id:
            select_entries[section].append(rule_id)
        elif action == "disable" and rule_id:
            ignore_entries[section].append(rule_id)
        elif action == "set" and parameter and value is not None:
            # Scalar config option: directly set in section
            # Try to convert to appropriate type
            config[section][parameter] = _convert_config_value(value)

    # Add list entries to each section
    for section in CONFIG_SECTIONS:
        if configure_entries[section]:
            config[section]["configure"] = configure_entries[section]
        if select_entries[section]:
            config[section]["select"] = select_entries[section]
        if ignore_entries[section]:
            config[section]["ignore"] = ignore_entries[section]

    return config


def _convert_config_value(value: str) -> bool | int | float | str:
    """
    Convert a string config value to the appropriate Python type.

    Args:
        value: The string value to convert.

    Returns:
        The converted value (bool, int, float, or str).

    """
    # Handle booleans
    if value.lower() in {"true", "yes", "on"}:
        return True
    if value.lower() in {"false", "no", "off"}:
        return False

    # Handle integers (try int first for values like "4" to stay as int)
    try:
        return int(value)
    except ValueError:
        pass

    # Handle floats (for values like "4.5" or "1e-3")
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value
