from __future__ import annotations

import fnmatch
import re
from enum import Enum
from pathlib import Path
from typing import Any

import typer
from typer._click.exceptions import FileError

try:
    import tomllib as toml  # type: ignore[import-not-found]
except ImportError:  # Python < 3.11
    import tomli as toml
from robot.errors import DataError

try:
    from robot.api import Languages  # RF 6.0
except ImportError:
    Languages = None

from robocop import exceptions, plugins
from robocop.linter.rules import RuleSeverity
from robocop.version_handling import ROBOT_VERSION, Version


class TargetVersion(Enum):
    RF4 = "4"
    RF5 = "5"
    RF6 = "6"
    RF7 = "7"

    @classmethod
    def from_string(cls, value: str) -> TargetVersion:
        try:
            return cls[f"RF{value}"]
        except KeyError:
            versions = ", ".join(ver.value for ver in TargetVersion)
            raise typer.BadParameter(
                f"Invalid target Robot Framework version: '{value}' is not one of {versions}"
            ) from None


def compile_rule_pattern(rule_pattern: str) -> re.Pattern[str]:
    return re.compile(fnmatch.translate(rule_pattern))


def validate_regex(value: str) -> re.Pattern[str]:
    try:
        return re.compile(value)
    except re.error:
        raise ValueError(f"'{value}' is not a valid regular expression.") from None


def parse_rule_severity(value: str) -> RuleSeverity:
    return RuleSeverity.parser(value, rule_severity=False)


VERBATIM_CONFIG_KEYS = frozenset({"variables", "per_file_ignores"})

BUILTIN_CONFIG_PREFIX = "robocop:"
"""Prefix used in the ``extends`` option to reference a built-in Robocop configuration (e.g. ``robocop:minimal``)."""

BUILTIN_CONFIG_DIR = Path(__file__).parent / "builtin"
"""Directory with the built-in Robocop configurations shipped with the package."""


def resolve_builtin_config(reference: str) -> Path:
    """
    Resolve a ``robocop:<name>`` reference to a built-in configuration file shipped with Robocop.

    Returns:
        Path to the built-in configuration file.

    """
    name = reference[len(BUILTIN_CONFIG_PREFIX) :]
    config_path = BUILTIN_CONFIG_DIR / f"{name}.toml"
    if not name or not config_path.is_file():
        available = ", ".join(sorted(path.stem for path in BUILTIN_CONFIG_DIR.glob("*.toml")))
        raise exceptions.ConfigurationError(
            f"Unknown built-in Robocop configuration: '{reference}'. Available built-in configurations: {available}."
        )
    return config_path


def normalize_config_keys(config: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize configuration keys to allow using both - and _ interchangeably.

    Keys of sections listed in ``VERBATIM_CONFIG_KEYS`` are user defined names (variable names, file patterns) and
    are never normalized.

    Returns:
        Configuration dictionary with normalized keys.

    """
    normalized: dict[str, Any] = {}
    for key, value in config.items():
        normalized_key = key.replace("-", "_")
        if isinstance(value, dict) and normalized_key not in VERBATIM_CONFIG_KEYS:
            normalized[normalized_key] = normalize_config_keys(value)
        else:
            normalized[normalized_key] = value
    return normalized


def load_languages(languages: list[str]) -> Languages | None:
    if Languages is None:
        return None
    try:
        return Languages(languages)
    except DataError:
        languages_str = ", ".join(languages)
        print(
            f"Failed to load languages: {languages_str}. "
            f"Verify if language is one of the supported languages: "
            f"https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#translations"
        )
        raise typer.Exit(code=1) from None


def validate_old_config(config_dict: dict[str, Any], config_path: Path) -> None:
    """Validate if the configuration file is not using old syntax."""
    old_options = {  # some options were deprecated, but most were moved into subdict (lint)
        "reports",
        "filetypesignore",
        "ignore_default",
        "threshold",
        "no_recursive",
        "persistent",
        "ext_rules",
        "configure",
        "output",
        "paths",
        "robotidy",
    }
    if isinstance(config_dict.get("format", {}), str) or any(key in old_options for key in config_dict):
        print(
            f"Configuration file seems to use Robocop < 6.0.0 or Robotidy syntax. "
            f"Please migrate the config: {config_path}"
        )
        raise typer.Exit(code=1)


def parse_target_version(value: int | str | TargetVersion | None) -> Version:
    if value is None:
        return ROBOT_VERSION
    if isinstance(value, TargetVersion):
        target_version = int(value.value)
    else:
        target_version = int(TargetVersion.from_string(str(value)).value)
    if target_version > ROBOT_VERSION.major:
        raise typer.BadParameter(
            f"Target Robot Framework version ({target_version}) should not be higher than "
            f"installed version ({ROBOT_VERSION})."
        ) from None
    return Version(f"{target_version}.0")


def parse_variables(variables: list[str] | None) -> dict[str, str] | None:
    """
    Parse variables provided with the ``--variable`` option.

    Variables use the ``NAME:VALUE`` syntax, same as in Robot Framework. Value may contain a colon.

    Returns:
        Mapping of variable name to its value, or None if no variable was provided.

    """
    if not variables:
        return None
    parsed: dict[str, str] = {}
    for variable in variables:
        name, separator, value = variable.partition(":")
        name = name.strip()
        if not separator or not name:
            raise typer.BadParameter(
                f"Invalid variable '{variable}'. Variable should be provided in the NAME:VALUE format."
            )
        parsed[name] = value
    return parsed


def resolve_relative_path(orig_path: str, config_dir: Path, ensure_exists: bool) -> str:
    """
    Resolve a given path relative to a configuration directory.

    If the path is absolute, it is returned as-is. If the path is relative, it is resolved
    relative to `config_dir`. Optionally, the method can ensure the resolved path exists
    before returning it.
    """
    path = Path(orig_path)
    if path.is_absolute():
        return orig_path
    resolved_path = config_dir / path
    if not ensure_exists or resolved_path.exists():
        return str(resolved_path)
    return orig_path


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            config: dict[str, Any] = toml.load(tf)
            return config
    except (toml.TOMLDecodeError, OSError) as e:
        raise FileError(filename=str(config_path), hint=f"Error reading configuration file: {e}") from None


def merge_dicts(dict1: dict[str, Any], dict2: dict[str, Any]) -> dict[str, Any]:
    """
    Merge two config dictionaries.

    Lists should be concatenated. The rest of the values should be overwritten.
    """
    for key, value in dict2.items():
        if key not in dict1 or type(value) != type(dict1[key]):  # noqa: E721
            dict1[key] = value
        elif isinstance(value, dict):
            dict1[key] = merge_dicts(dict1[key], value)
        elif isinstance(value, list):
            dict1[key].extend(value)
        else:
            dict1[key] = value
    return dict1


def extend_configs(config: dict[str, Any], config_path: Path, seen: set[Path]) -> dict[str, Any]:
    """Extend configuration files with the configs from the extends option."""
    if "extends" not in config:
        return config
    merged_config: dict[str, Any] = {}
    for base_config in config["extends"]:
        if not isinstance(base_config, str):
            raise exceptions.ConfigurationError(
                f"Invalid 'extends' parameter value in the configuration file: '{config_path}'. "
                f"{base_config} is not a string."
            )
        if base_config.startswith(BUILTIN_CONFIG_PREFIX):
            extended_path = resolve_builtin_config(base_config)
        elif not base_config.endswith(".toml"):
            extended_path = plugins.resolve_path_reference(base_config)
            if not extended_path.is_file():
                raise exceptions.ConfigurationError(
                    f"Configuration '{base_config}' referenced in the 'extends' parameter in the configuration "
                    f"file: '{config_path}' does not exist. Expected plugin file: '{extended_path}'."
                )
        else:
            base_config_path = Path(base_config)
            if base_config_path.is_absolute():
                extended_path = base_config_path
            else:
                extended_path = (config_path.parent / base_config_path).resolve()
        if extended_path in seen:
            raise exceptions.CircularExtendsReferenceError(str(config_path)) from None
        normalized_config = read_robocop_toml_config(extended_path)
        extended_config = extend_configs(normalized_config, extended_path, seen={*seen, extended_path})
        merged_config = merge_dicts(merged_config, extended_config)
    return merge_dicts(merged_config, config)


def read_robocop_toml_config(config_path: Path) -> dict[str, Any]:
    """
    Load and return toml configuration file.

    For pyproject.toml files we need to retrieve configuration from [tool.robocop] section. This section is not
    required for the robocop.toml file.
    """
    config = load_toml_file(config_path)
    if config_path.name == "robocop.toml":
        if tool_config := config.get("tool", {}).get("robocop", {}):
            config = tool_config
    else:
        config = config.get("tool", {}).get("robocop", {})
    if not config:
        return {}
    return {k.replace("-", "_"): v for k, v in config.items()}


def read_toml_config(config_path: Path) -> dict[str, Any] | None:
    """Load configuration file and extend it with configs from extends option."""
    normalized_config = read_robocop_toml_config(config_path)
    return extend_configs(normalized_config, config_path, seen=set())
