"""
Natural language configuration parser for Robocop.

This module provides functions to parse natural language descriptions into
Robocop configuration suggestions. It builds a rule catalog and system message
for LLM-assisted configuration generation.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, TypedDict

from robocop.mcp.tools.models import ApplyConfigurationResult, ConfigSuggestion, NLConfigResult
from robocop.mcp.tools.utils.constants import NESTED_CONFIG_SECTIONS
from robocop.mcp.tools.utils.helpers import (
    ConfigOptionsCatalog,
    RuleCatalogEntry,
    RuleParamInfo,
    SuggestionDict,
    build_config_options_catalog,
    build_rule_catalog,
    detect_config_conflicts,
    generate_toml_config_from_suggestions,
    get_rule_by_name_or_id,
    validate_rule_param,
)
from robocop.mcp.tools.utils.toml_handler import (
    TOMLDecodeError,
    extract_all_sections_string,
    generate_diff,
    is_robocop_toml,
    merge_robocop_section,
    parse_toml_string,
    read_toml_file,
    toml_to_string,
    write_toml_file,
)

# --- Type Definitions ---


class RawSuggestion(TypedDict, total=False):
    """
    Raw suggestion from LLM response before validation.

    All fields are optional since we need to validate their presence.
    """

    rule_id: str
    rule_name: str
    action: str
    parameter: str
    value: str
    section: str
    interpretation: str
    explanation: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of validating raw suggestions from LLM response."""

    suggestions: tuple[ConfigSuggestion, ...]
    warnings: tuple[str, ...]

    @classmethod
    def empty(cls, warnings: list[str] | None = None) -> ValidationResult:
        """
        Create an empty result with optional warnings.

        Args:
            warnings: Optional list of warning messages.

        Returns:
            A ValidationResult with no suggestions.

        """
        return cls(
            suggestions=(),
            warnings=tuple(warnings) if warnings else (),
        )


@dataclass(frozen=True, slots=True)
class _SuggestionContext:
    """Parsed context from a raw suggestion for validation."""

    action: str
    section: str
    parameter: str | None
    value: str | None
    interpretation: str
    explanation: str


# --- Helper Functions ---


def _exclude_keys(d: dict[str, Any], keys: frozenset[str]) -> dict[str, Any]:
    """
    Return a copy of dict d without the specified keys.

    Args:
        d: The source dictionary.
        keys: Frozenset of keys to exclude.

    Returns:
        A new dictionary with the specified keys removed.

    """
    return {k: v for k, v in d.items() if k not in keys}


def _format_rule_parameters(params: list[RuleParamInfo], rule_name: str) -> list[str]:
    """
    Format rule parameters with an example configuration line.

    Args:
        params: List of parameter info dicts with name, type, default keys.
        rule_name: The rule name for the example.

    Returns:
        List of formatted parameter lines.

    """
    lines: list[str] = []
    param_strs = [
        f"{p['name']} ({p['type']}, default={p['default']})" if p.get("default") else f"{p['name']} ({p['type']})"
        for p in params
    ]
    lines.append(f"  Parameters: {'; '.join(param_strs)}")

    # Add example configuration using the first parameter
    first_param = params[0]
    example_value = first_param.get("default", "value")
    lines.append(f'  Example: configure = ["{rule_name}.{first_param["name"]}={example_value}"]')

    return lines


def _format_rule_entry(rule: RuleCatalogEntry) -> list[str]:
    """
    Format a single rule entry for the system message.

    Args:
        rule: Rule catalog entry with rule_id, name, description, deprecated, enabled, parameters.

    Returns:
        List of formatted lines for this rule.

    """
    lines: list[str] = []

    deprecated_marker = " [DEPRECATED]" if rule.get("deprecated") else ""
    enabled_marker = "" if rule.get("enabled") else " [disabled by default]"
    lines.append(f"- {rule['rule_id']} ({rule['name']}){deprecated_marker}{enabled_marker}: {rule['description']}")

    params = rule.get("parameters", [])
    if params:
        lines.extend(_format_rule_parameters(params, rule["name"]))

    return lines


def _build_rules_section(rule_catalog: list[RuleCatalogEntry]) -> str:
    """
    Build the rules section of the system message, grouped by category.

    Args:
        rule_catalog: List of rule catalog entries from build_rule_catalog().

    Returns:
        Formatted string with all rules grouped by category.

    """
    # Group rules by category prefix (letters before digits)
    categories: dict[str, list[RuleCatalogEntry]] = defaultdict(list)
    for rule in rule_catalog:
        category = "".join(c for c in rule["rule_id"] if c.isalpha())
        categories[category].append(rule)

    lines: list[str] = []
    for category in sorted(categories):
        category_name = _get_category_name(category)
        lines.append(f"\n## {category_name} ({category})")

        for rule in categories[category]:
            lines.extend(_format_rule_entry(rule))

    return "\n".join(lines)


def _build_config_options_section(config_catalog: ConfigOptionsCatalog) -> str:
    """
    Build the configuration options section of the system message.

    Args:
        config_catalog: Config options catalog with 'common', 'lint', 'format' sections.

    Returns:
        Formatted string with all config options by section.

    """
    section_headers = [
        ("common", "## Common Options [tool.robocop]"),
        ("lint", "\n## Lint Options [tool.robocop.lint]"),
        ("format", "\n## Formatter Options [tool.robocop.format]"),
    ]

    lines = ["\n# Configuration Options\n"]
    for section_key, header in section_headers:
        lines.append(header)
        for opt in config_catalog.get(section_key, []):
            lines.append(f"- {opt['name']}: {opt['type']} (default: {opt['default']})")

    return "\n".join(lines)


def _build_system_message(
    rule_catalog: list[RuleCatalogEntry],
    config_catalog: ConfigOptionsCatalog | None = None,
) -> str:
    """
    Build the system message with rule catalog and config options for LLM context.

    Args:
        rule_catalog: The rule catalog from build_rule_catalog().
        config_catalog: The config options catalog from build_config_options_catalog().

    Returns:
        A formatted system message string with all rules, config options, and instructions.

    """
    rules_text = _build_rules_section(rule_catalog)
    config_section = _build_config_options_section(config_catalog) if config_catalog else ""

    return f"""You are a Robocop configuration assistant.
Robocop is a static code analyzer and formatter for Robot Framework with {len(rule_catalog)} rules.

# Available Rules
{rules_text}
{config_section}

# Configuration Format

TOML syntax uses different sections:
- [tool.robocop] for common options (cache, language, verbose, etc.)
- [tool.robocop.lint] for linter rules and settings
- [tool.robocop.format] for formatter settings (space_count, indent, line_length, etc.)

## Rule Configuration (in [tool.robocop.lint]):
1. Configure rule parameters:
   configure = ["rule-name.param=value", "another-rule.param=value"]
2. Enable specific rules:
   select = ["RULE_ID", "another-rule"]
3. Disable rules:
   ignore = ["RULE_ID", "another-rule"]

## Scalar Options (use action="set"):
- cache_dir = "/path/to/cache"
- target_version = 7
- line_length = 120
- space_count = 4

# Your Task

Parse the user's natural language request and suggest configuration changes.

Rules:
- Match user descriptions to specific rules by name, ID, or description
- For general config options (cache, formatting settings), use action="set"
- If the user wants to "allow" something, they usually want to increase a limit or disable a rule
- If the user wants to "enforce" or "require" something, they want to enable or configure a rule
- Handle ambiguous requests by picking the most likely match and noting the ambiguity

Respond with ONLY valid JSON (no markdown code blocks, no extra text):
{{
  "interpretation": "Brief summary of what you understood the user wanted",
  "suggestions": [
    {{
      "rule_id": "LEN08",
      "rule_name": "line-too-long",
      "action": "configure",
      "parameter": "line_length",
      "value": "140",
      "section": "lint",
      "interpretation": "Allow lines up to 140 characters",
      "explanation": "The line-too-long rule defaults to 120 chars; setting to 140 as requested"
    }},
    {{
      "action": "set",
      "parameter": "cache_dir",
      "value": "/tmp/robocop-cache",
      "section": "common",
      "interpretation": "Set cache directory",
      "explanation": "Store cache files in the specified directory"
    }}
  ],
  "warnings": ["any ambiguities, assumptions, or issues to note"]
}}

Actions:
- "configure": Set a rule parameter (requires rule_id, rule_name, parameter, value, section="lint")
- "enable": Add rule to select list (requires rule_id, rule_name, section="lint")
- "disable": Add rule to ignore list (requires rule_id, rule_name, section="lint")
- "set": Set a scalar config option (requires parameter, value, section="common"|"lint"|"format")

# CLI-Only Options (NOT configurable via TOML)
Some options are only available via command-line flags and CANNOT be set in configuration files:
- --ignore-git-dir: Ignore .git directories when finding project root
- --ignore-file-config: Don't load configuration files
- --skip-gitignore: Don't skip files listed in .gitignore
- --force-exclude: Enforce exclusions for directly passed paths
- --config: Path to configuration file
- --root: Project root directory

If user asks about these, add a warning that they are CLI-only options."""


def _get_category_name(category: str) -> str:
    """
    Get a human-readable name for a rule category.

    Args:
        category: The category prefix (e.g., "LEN", "NAME").

    Returns:
        A human-readable category name.

    """
    category_names = {
        "ARG": "Argument Rules",
        "COM": "Comment Rules",
        "DEPR": "Deprecation Rules",
        "DOC": "Documentation Rules",
        "DUP": "Duplication Rules",
        "ERR": "Error Rules",
        "IMP": "Import Rules",
        "KW": "Keyword Rules",
        "LEN": "Length Rules",
        "MISC": "Miscellaneous Rules",
        "NAME": "Naming Rules",
        "ORD": "Ordering Rules",
        "SPC": "Spacing Rules",
        "TAG": "Tag Rules",
        "VAR": "Variable Rules",
        "ANN": "Annotation Rules",
    }
    return category_names.get(category, f"{category} Rules")


def _strip_markdown_code_block(text: str) -> str:
    """
    Remove markdown code block delimiters if present.

    Handles both ``` and ~~~ style code blocks, with optional language specifier.

    Args:
        text: The text potentially wrapped in markdown code blocks.

    Returns:
        The text with code block delimiters removed.

    """
    lines = text.strip().split("\n")
    if not lines:
        return text

    # Check for opening delimiter (``` or ~~~, optionally followed by language)
    first_line = lines[0].strip()
    if first_line.startswith(("```", "~~~")):
        delimiter = first_line[:3]
        lines = lines[1:]  # Remove opening line

        # Check for closing delimiter
        if lines and lines[-1].strip() == delimiter:
            lines = lines[:-1]

    return "\n".join(lines)


def _parse_llm_response(response: str) -> tuple[dict[str, Any], str | None]:
    """
    Parse the LLM's JSON response.

    Args:
        response: The raw response string from the LLM.

    Returns:
        A tuple of (parsed_dict, error_message).
        If parsing fails, returns ({}, error_message).

    """
    cleaned = _strip_markdown_code_block(response)

    try:
        return json.loads(cleaned), None
    except json.JSONDecodeError as e:
        return {}, f"Failed to parse LLM response as JSON: {e}"


def _validate_suggestions(raw_suggestions: list[RawSuggestion]) -> ValidationResult:
    """
    Validate and convert raw suggestions to ConfigSuggestion models.

    Args:
        raw_suggestions: List of suggestion dicts from LLM response.

    Returns:
        ValidationResult containing valid suggestions and any warnings.

    """
    valid_suggestions: list[ConfigSuggestion] = []
    warnings: list[str] = []

    for raw in raw_suggestions:
        suggestion = _validate_single_suggestion(raw, warnings)
        if suggestion is not None:
            valid_suggestions.append(suggestion)

    return ValidationResult(
        suggestions=tuple(valid_suggestions),
        warnings=tuple(warnings),
    )


def _parse_suggestion_context(raw: RawSuggestion, warnings: list[str]) -> _SuggestionContext:
    """
    Parse and validate the common fields from a raw suggestion.

    Args:
        raw: Raw suggestion dict from LLM response.
        warnings: List to append warnings to (mutated in place).

    Returns:
        Parsed suggestion context with validated section.

    """
    section = raw.get("section", "lint")

    # Validate section
    if section not in {"common", "lint", "format"}:
        warnings.append(f"Invalid section '{section}', defaulting to 'lint'")
        section = "lint"

    return _SuggestionContext(
        action=raw.get("action", "configure"),
        section=section,
        parameter=raw.get("parameter"),
        value=raw.get("value"),
        interpretation=raw.get("interpretation", ""),
        explanation=raw.get("explanation", ""),
    )


def _validate_single_suggestion(
    raw: RawSuggestion,
    warnings: list[str],
) -> ConfigSuggestion | None:
    """
    Validate a single raw suggestion and convert to ConfigSuggestion.

    Args:
        raw: Raw suggestion dict from LLM response.
        warnings: List to append warnings to (mutated in place).

    Returns:
        ConfigSuggestion if valid, None if invalid.

    """
    ctx = _parse_suggestion_context(raw, warnings)

    # Handle "set" action for scalar config options
    if ctx.action == "set":
        return _validate_set_action(ctx, warnings)

    # For rule-based actions (configure, enable, disable)
    return _validate_rule_action(raw, ctx, warnings)


def _validate_set_action(
    ctx: _SuggestionContext,
    warnings: list[str],
) -> ConfigSuggestion | None:
    """
    Validate and create a 'set' action suggestion.

    Args:
        ctx: Parsed suggestion context.
        warnings: List to append warnings to.

    Returns:
        ConfigSuggestion if valid, None if invalid.

    """
    if not ctx.parameter or ctx.value is None:
        warnings.append("Set action missing parameter or value, skipping")
        return None

    return ConfigSuggestion(
        rule_id=None,
        rule_name=None,
        action="set",
        parameter=ctx.parameter,
        value=str(ctx.value),
        section=ctx.section,
        interpretation=ctx.interpretation,
        explanation=ctx.explanation,
    )


def _validate_rule_action(
    raw: RawSuggestion,
    ctx: _SuggestionContext,
    warnings: list[str],
) -> ConfigSuggestion | None:
    """
    Validate and create a rule-based action suggestion.

    Args:
        raw: Raw suggestion dict (for rule_id/rule_name).
        ctx: Parsed suggestion context.
        warnings: List to append warnings to.

    Returns:
        ConfigSuggestion if valid, None if invalid.

    """
    rule_id = raw.get("rule_id", "")
    rule_name = raw.get("rule_name", "")

    # Validate rule exists
    rule = get_rule_by_name_or_id(rule_name) or get_rule_by_name_or_id(rule_id)
    if rule is None:
        warnings.append(f"Rule '{rule_name or rule_id}' not found, skipping")
        return None

    # Use canonical names
    canonical_id = rule.rule_id
    canonical_name = rule.name

    # Validate action
    if ctx.action not in {"configure", "enable", "disable"}:
        warnings.append(f"Invalid action '{ctx.action}' for rule '{canonical_name}', skipping")
        return None

    # Validate parameter for configure action
    if ctx.action == "configure":
        if not ctx.parameter or not ctx.value:
            warnings.append(f"Configure action for '{canonical_name}' missing parameter or value, skipping")
            return None

        is_valid, _, error = validate_rule_param(canonical_name, ctx.parameter, str(ctx.value))
        if not is_valid:
            warnings.append(error or f"Invalid parameter configuration for '{canonical_name}'")
            return None

    # Check for deprecated rules
    if rule.deprecated:
        warnings.append(f"Rule '{canonical_name}' ({canonical_id}) is deprecated")

    return ConfigSuggestion(
        rule_id=canonical_id,
        rule_name=canonical_name,
        action=ctx.action,
        parameter=ctx.parameter if ctx.action == "configure" else None,
        value=str(ctx.value) if ctx.action == "configure" and ctx.value else None,
        section=ctx.section,
        interpretation=ctx.interpretation,
        explanation=ctx.explanation,
    )


def _parse_config_impl(
    llm_response: str | None = None,
) -> NLConfigResult:
    """
    Parse LLM response into configuration suggestions.

    This function validates and converts the LLM's JSON response
    into structured configuration suggestions.

    Args:
        llm_response: The JSON response from the LLM after processing user's description.

    Returns:
        NLConfigResult with suggestions and TOML config.

    """
    warnings: list[str] = []

    if llm_response is None:
        # No LLM response provided - this shouldn't happen in normal flow
        # The host LLM should process the description using the system message
        return NLConfigResult(
            success=False,
            suggestions=[],
            toml_config="",
            warnings=["No LLM response provided. Use the system message to process the description."],
            explanation="Configuration parsing requires LLM processing.",
        )

    # Parse the LLM response
    parsed, parse_error = _parse_llm_response(llm_response)
    if parse_error:
        warnings.append(parse_error)
        return NLConfigResult(
            success=False,
            suggestions=[],
            toml_config="",
            warnings=warnings,
            explanation="Failed to parse configuration suggestions.",
        )

    # Extract and validate suggestions
    raw_suggestions = parsed.get("suggestions", [])
    interpretation = parsed.get("interpretation", "")
    llm_warnings = parsed.get("warnings", [])

    validation_result = _validate_suggestions(raw_suggestions)
    warnings.extend(llm_warnings)
    warnings.extend(validation_result.warnings)

    # Detect conflicts (only for rule-based suggestions)
    suggestion_dicts: list[SuggestionDict] = [
        {
            "rule_id": s.rule_id or "",
            "rule_name": s.rule_name or "",
            "action": s.action,
            "parameter": s.parameter or "",
            "value": s.value or "",
            "section": s.section,
        }
        for s in validation_result.suggestions
    ]
    conflict_warnings = detect_config_conflicts(suggestion_dicts)
    warnings.extend(conflict_warnings)

    # Generate TOML config for all sections
    config_sections = generate_toml_config_from_suggestions(suggestion_dicts)
    toml_config = extract_all_sections_string(config_sections)

    return NLConfigResult(
        success=len(validation_result.suggestions) > 0,
        suggestions=list(validation_result.suggestions),
        toml_config=toml_config,
        warnings=warnings,
        explanation=interpretation or "Generated configuration from natural language description.",
    )


def get_config_system_message() -> str:
    """
    Get the system message for natural language configuration.

    This is used by the MCP tool to provide context to the host LLM.

    Returns:
        The system message string with all rules, config options, and instructions.

    """
    rule_catalog = build_rule_catalog()
    config_catalog = build_config_options_catalog()
    return _build_system_message(rule_catalog, config_catalog)


def parse_config_from_llm_response(llm_response: str) -> NLConfigResult:
    """
    Parse an LLM response into configuration suggestions.

    This is the main entry point for the MCP tool after the host LLM
    has processed the user's description.

    Args:
        llm_response: The JSON response from the LLM.

    Returns:
        NLConfigResult with validated suggestions and TOML config.

    """
    return _parse_config_impl(llm_response=llm_response)


def _validate_configure_entries(entries: list[str]) -> str | None:
    """
    Validate configure entry formats (rule.param=value).

    Returns:
        error message if invalid, None if all valid.

    """
    for entry in entries:
        try:
            _rule_name, param_value = entry.split(".", maxsplit=1)
            _param, _value = param_value.split("=", maxsplit=1)
        except ValueError:
            return f"Invalid configure entry format: {entry}"
    return None


def _parse_toml_config_all_sections(
    toml_config: str,
) -> tuple[dict[str, dict[str, Any]], str | None]:
    """
    Parse TOML config string into section dicts. Returns (sections, error).

    Handles both formats:
    - [tool.robocop.*] (for pyproject.toml/robot.toml)
    - Root level / [lint] / [format] (for robocop.toml)

    Returns:
        A tuple of (sections_dict, error). sections_dict has keys 'common', 'lint', 'format'.

    """
    sections: dict[str, dict[str, Any]] = {"common": {}, "lint": {}, "format": {}}

    try:
        config = parse_toml_string(toml_config)

        # Try [tool.robocop.*] first (pyproject.toml/robot.toml format)
        robocop_config = config.get("tool", {}).get("robocop", {})
        if robocop_config:
            # Extract sections from tool.robocop
            sections["lint"] = robocop_config.get("lint", {})
            sections["format"] = robocop_config.get("format", {})
            sections["common"] = _exclude_keys(robocop_config, NESTED_CONFIG_SECTIONS)
            return sections, None

        # Try root level sections (robocop.toml format)
        sections["lint"] = config.get("lint", {})
        sections["format"] = config.get("format", {})
        sections["common"] = _exclude_keys(config, NESTED_CONFIG_SECTIONS)

        return sections, None
    except TOMLDecodeError as e:
        return sections, f"Invalid TOML: {e}"


def _extract_display_sections(config: dict[str, Any], use_root_level: bool) -> dict[str, dict[str, Any]]:
    """
    Extract display sections from a merged config.

    Args:
        config: The merged configuration dictionary.
        use_root_level: If True, sections are at root level (robocop.toml format).
                       If False, sections are under tool.robocop (pyproject.toml format).

    Returns:
        A dict with 'common', 'lint', and 'format' sections.

    """
    if use_root_level:
        source = config
    else:
        source = config.get("tool", {}).get("robocop", {})

    return {
        "common": _exclude_keys(source, NESTED_CONFIG_SECTIONS),
        "lint": source.get("lint", {}),
        "format": source.get("format", {}),
    }


def _make_error_result(file_path: Path, error: str) -> ApplyConfigurationResult:
    """
    Create a standardized error result for configuration application.

    Args:
        file_path: The path to the configuration file.
        error: The error message.

    Returns:
        ApplyConfigurationResult indicating failure.

    """
    return ApplyConfigurationResult(
        success=False,
        file_path=str(file_path),
        file_created=False,
        diff=None,
        merged_config="",
        validation_passed=False,
        validation_error=error,
    )


def _apply_config_impl(
    toml_config: str,
    file_path: str = "pyproject.toml",
) -> ApplyConfigurationResult:
    """
    Apply configuration to a file.

    Supports three configuration file formats:
    - pyproject.toml: Uses [tool.robocop.*] sections
    - robot.toml: Uses [tool.robocop.*] sections
    - robocop.toml: Uses root level / [lint] / [format] (no [tool.robocop] prefix)

    Args:
        toml_config: The TOML configuration string to apply.
        file_path: Path to the configuration file (default: pyproject.toml).

    Returns:
        ApplyConfigurationResult with success status and details.

    """
    path = Path(file_path).resolve()
    file_existed = path.exists()
    use_root_level = is_robocop_toml(path)

    try:
        # Parse new config into sections
        new_sections, parse_error = _parse_toml_config_all_sections(toml_config)
        if parse_error:
            return _make_error_result(path, parse_error)

        # Read existing config
        existing_config = read_toml_file(path)
        existing_toml = toml_to_string(existing_config) if existing_config else ""

        # Merge each section
        merged_config = dict(existing_config)
        for section_name, section_config in new_sections.items():
            if section_config:  # Only merge non-empty sections
                merged_config = merge_robocop_section(merged_config, section_config, section_name, use_root_level)

        # Generate diff and write file
        diff = generate_diff(existing_toml, toml_to_string(merged_config), path.name)
        write_toml_file(path, merged_config)

        # Extract all sections for display
        display_sections = _extract_display_sections(merged_config, use_root_level)

        # Validate configure entries in lint section
        lint_section = display_sections.get("lint", {})
        validation_error = _validate_configure_entries(lint_section.get("configure", []))

        return ApplyConfigurationResult(
            success=True,
            file_path=str(path),
            file_created=not file_existed,
            diff=diff,
            merged_config=extract_all_sections_string(display_sections, use_root_level=use_root_level),
            validation_passed=validation_error is None,
            validation_error=validation_error,
        )

    except PermissionError:
        return _make_error_result(path, f"Permission denied: Cannot write to {path}")
    except OSError as e:
        return _make_error_result(path, str(e))
