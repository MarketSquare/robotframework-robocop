"""
TOML file handler for natural language configuration.

Provides utilities for reading, merging, and writing TOML configuration files,
specifically for Robocop's configuration sections.

Uses tomlkit to preserve comments and formatting when modifying existing files.

Robocop supports three configuration file formats:
- pyproject.toml: Uses [tool.robocop] section
- robot.toml: Uses [tool.robocop] section
- robocop.toml: Uses root level (no [tool.robocop] prefix needed), but also accepts [tool.robocop]
"""

from __future__ import annotations

import difflib
from pathlib import Path  # noqa: TC003 - used at runtime
from typing import Any

import tomlkit
from tomlkit import TOMLDocument
from tomlkit.exceptions import TOMLKitError

from robocop.mcp.tools.utils.constants import CONFIG_NAMES

# Re-export for backwards compatibility
TOMLDecodeError = TOMLKitError

__all__ = ["CONFIG_NAMES", "TOMLDecodeError"]


def is_robocop_toml(path: Path) -> bool:
    """
    Check if the path is a robocop.toml file (uses root-level config).

    Args:
        path: Path to the TOML file.

    Returns:
        True if the file is named robocop.toml, False otherwise.

    """
    return path.name == "robocop.toml"


def read_toml_file(path: Path) -> TOMLDocument:
    """
    Read and parse a TOML file, preserving comments and formatting.

    Args:
        path: Path to the TOML file.

    Returns:
        Parsed TOML as a TOMLDocument (dict-like). Returns empty document if file doesn't exist.

    """
    if not path.exists():
        return tomlkit.document()

    with path.open("r", encoding="utf-8") as f:
        return tomlkit.parse(f.read())


def read_toml_file_as_string(path: Path) -> str:
    """
    Read a TOML file as a raw string.

    Args:
        path: Path to the TOML file.

    Returns:
        File contents as string, or empty string if file doesn't exist.

    """
    if not path.exists():
        return ""

    with path.open("r", encoding="utf-8") as f:
        return f.read()


def write_toml_file(path: Path, config: TOMLDocument | dict[str, Any]) -> None:
    """
    Write a TOML document to a file, preserving comments and formatting.

    Args:
        path: Path to the TOML file.
        config: TOMLDocument or dictionary to write as TOML.

    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(tomlkit.dumps(config))


def merge_robocop_config(
    existing: TOMLDocument | dict[str, Any],
    new_lint_config: dict[str, Any],
    use_root_level: bool = False,
) -> TOMLDocument | dict[str, Any]:
    """
    Merge new Robocop lint configuration with existing config.

    This function merges configuration at the appropriate level based on file type:
    - For pyproject.toml/robot.toml: [tool.robocop.lint]
    - For robocop.toml: [lint] at root level

    Intelligently combines lists (like `configure`, `select`, `ignore`)
    and overwrites scalar values. Preserves comments and formatting.

    Args:
        existing: The existing full TOML config (may be empty).
        new_lint_config: The new lint configuration to merge (just the lint section contents).
        use_root_level: If True, use root level [lint] section (for robocop.toml).
                       If False, use [tool.robocop.lint] (for pyproject.toml/robot.toml).

    Returns:
        The merged configuration with the lint section updated.

    """
    return merge_robocop_section(existing, new_lint_config, "lint", use_root_level)


def merge_robocop_section(
    existing: TOMLDocument | dict[str, Any],
    new_config: dict[str, Any],
    section: str = "lint",
    use_root_level: bool = False,
) -> TOMLDocument | dict[str, Any]:
    """
    Merge new Robocop configuration with existing config for any section.

    This function merges configuration at the appropriate level based on file type and section:
    - For pyproject.toml/robot.toml: [tool.robocop], [tool.robocop.lint], [tool.robocop.format]
    - For robocop.toml: root level, [lint], [format]

    Preserves comments and formatting in the existing document.

    Args:
        existing: The existing full TOML config (may be empty).
        new_config: The new configuration to merge (just the section contents).
        section: Which section to merge into: "common" (root), "lint", or "format".
        use_root_level: If True, use root level (for robocop.toml).
                       If False, use [tool.robocop.*] (for pyproject.toml/robot.toml).

    Returns:
        The merged configuration with the section updated.

    """
    # Work with the existing document to preserve comments
    existing_section = _get_or_create_section(existing, section, use_root_level)
    _merge_section_values(existing_section, new_config)
    return existing


def _get_or_create_section(config: TOMLDocument | dict[str, Any], section: str, use_root_level: bool) -> dict[str, Any]:
    """
    Get or create the appropriate section in the config dict.

    Args:
        config: The configuration dictionary to modify in place.
        section: Which section: "common", "lint", or "format".
        use_root_level: If True, use root level paths.

    Returns:
        Reference to the section dict (modifying it modifies config).

    """
    if use_root_level:
        # For robocop.toml: root level or [lint]/[format]
        if section == "common":
            return config
        if section not in config:
            config[section] = tomlkit.table()
        return config[section]

    # For pyproject.toml/robot.toml: [tool.robocop.*]
    if "tool" not in config:
        config["tool"] = tomlkit.table()
    if "robocop" not in config["tool"]:
        config["tool"]["robocop"] = tomlkit.table()

    if section == "common":
        return config["tool"]["robocop"]

    if section not in config["tool"]["robocop"]:
        config["tool"]["robocop"][section] = tomlkit.table()
    return config["tool"]["robocop"][section]


def _merge_section_values(existing: dict[str, Any], new_config: dict[str, Any]) -> None:
    """
    Merge new values into existing section, handling lists specially.

    Args:
        existing: The existing section dict (modified in place).
        new_config: The new values to merge.

    """
    # List fields that should be merged (not replaced)
    list_fields = {
        "configure",
        "select",
        "extend_select",
        "ignore",
        "custom_rules",
        "reports",
        "include",
        "exclude",
        "language",
    }

    for key, new_value in new_config.items():
        if key in list_fields and isinstance(new_value, list):
            # Merge lists, avoiding duplicates while preserving order
            existing_values = existing.get(key, [])
            if not isinstance(existing_values, list):
                existing_values = [existing_values] if existing_values else []
            # Convert to regular list for manipulation
            existing_values = list(existing_values)

            # For 'configure', we need smarter merging (same rule.param should be replaced)
            if key == "configure":
                merged = _merge_configure_lists(existing_values, new_value)
            else:
                # Simple deduplication for other lists
                seen = set()
                merged = []
                for item in existing_values + new_value:
                    if item not in seen:
                        seen.add(item)
                        merged.append(item)
            existing[key] = merged
        else:
            # Scalar values: new overwrites existing
            existing[key] = new_value


def _merge_configure_lists(existing: list[str], new: list[str]) -> list[str]:
    """
    Merge configure lists, replacing entries for the same rule.param.

    For example, if existing has "line-too-long.line_length=120" and new has
    "line-too-long.line_length=140", the result will have only the new value.

    Args:
        existing: Existing configure entries.
        new: New configure entries.

    Returns:
        Merged list with newer values taking precedence.

    """
    # Build a dict keyed by "rule.param" to track the latest value
    config_dict: dict[str, str] = {}

    for entry in existing:
        key = _get_configure_key(entry)
        config_dict[key] = entry

    for entry in new:
        key = _get_configure_key(entry)
        config_dict[key] = entry  # New value overwrites

    return list(config_dict.values())


def _get_configure_key(entry: str) -> str:
    """
    Extract the rule.param key from a configure entry.

    Args:
        entry: A configure entry like "rule-name.param=value"

    Returns:
        The key "rule-name.param" or the full entry if malformed.

    """
    if "=" in entry:
        return entry.split("=", 1)[0]
    return entry


def generate_diff(before: str, after: str, filename: str = "pyproject.toml") -> str | None:
    """
    Generate a unified diff between two strings.

    Args:
        before: The original content.
        after: The modified content.
        filename: The filename to show in the diff header.

    Returns:
        A unified diff string, or None if there are no changes.

    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    diff_lines = list(
        difflib.unified_diff(
            before_lines,
            after_lines,
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )

    if not diff_lines:
        return None

    return "".join(diff_lines)


def toml_to_string(config: TOMLDocument | dict[str, Any]) -> str:
    """
    Convert a dictionary or TOMLDocument to a TOML string.

    Args:
        config: Dictionary or TOMLDocument to convert.

    Returns:
        TOML-formatted string.

    """
    return tomlkit.dumps(config)


def parse_toml_string(toml_str: str) -> TOMLDocument:
    """
    Parse a TOML string into a TOMLDocument.

    Args:
        toml_str: The TOML string to parse.

    Returns:
        Parsed TOMLDocument. Raises TOMLKitError if the string is invalid TOML.

    """
    return tomlkit.parse(toml_str)


def extract_lint_section_string(lint_config: dict[str, Any], use_root_level: bool = False) -> str:
    """
    Generate a TOML string for the lint section.

    Args:
        lint_config: The lint configuration dictionary (contents only, not nested).
        use_root_level: If True, generate [lint] section (for robocop.toml).
                       If False, generate [tool.robocop.lint] (for pyproject.toml/robot.toml).

    Returns:
        A TOML string with the appropriate header.

    """
    if not lint_config:
        return "[lint]\n" if use_root_level else "[tool.robocop.lint]\n"

    return toml_to_string({"lint": lint_config} if use_root_level else {"tool": {"robocop": {"lint": lint_config}}})


def extract_all_sections_string(config_sections: dict[str, dict[str, Any]], use_root_level: bool = False) -> str:
    """
    Generate a TOML string for all Robocop config sections.

    Args:
        config_sections: Dict with keys 'common', 'lint', 'format', each containing config.
        use_root_level: If True, generate root level sections (for robocop.toml).
                       If False, generate [tool.robocop.*] (for pyproject.toml/robot.toml).

    Returns:
        A TOML string with all non-empty sections.

    """
    common = config_sections.get("common", {})
    lint = config_sections.get("lint", {})
    fmt = config_sections.get("format", {})

    if use_root_level:
        # robocop.toml: root level for common, [lint] for lint, [format] for format
        result: dict[str, Any] = {}
        result.update(common)
        if lint:
            result["lint"] = lint
        if fmt:
            result["format"] = fmt
        return toml_to_string(result) if result else ""

    # pyproject.toml/robot.toml: [tool.robocop.*]
    robocop_section: dict[str, Any] = {}
    robocop_section.update(common)
    if lint:
        robocop_section["lint"] = lint
    if fmt:
        robocop_section["format"] = fmt

    if not robocop_section:
        return ""

    return toml_to_string({"tool": {"robocop": robocop_section}})


def has_robocop_config(config: TOMLDocument | dict[str, Any], use_root_level: bool) -> bool:
    """
    Check if Robocop configuration already exists in the config.

    Args:
        config: The parsed TOML configuration.
        use_root_level: If True, check for root-level [lint]/[format] (robocop.toml).
                       If False, check for [tool.robocop] (pyproject.toml/robot.toml).

    Returns:
        True if Robocop config exists, False otherwise.

    """
    if use_root_level:
        # For robocop.toml, check for [lint] or [format] sections
        return "lint" in config or "format" in config

    # For pyproject.toml/robot.toml, check for [tool.robocop]
    tool = config.get("tool", {})
    return "robocop" in tool


def append_config_to_file_content(existing_content: str, new_config: str) -> str:
    """
    Append new configuration to the end of existing file content.

    Ensures proper formatting with appropriate newlines between sections.

    Args:
        existing_content: The existing file content (may be empty).
        new_config: The new TOML configuration to append.

    Returns:
        The combined content with new config appended at the end.

    """
    if not existing_content:
        return new_config

    if not new_config:
        return existing_content

    # Ensure existing content ends with newline
    result = existing_content
    if not result.endswith("\n"):
        result += "\n"

    # Add blank line before new section for readability (if not already present)
    if not result.endswith("\n\n"):
        result += "\n"

    return result + new_config
