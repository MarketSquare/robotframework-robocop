from __future__ import annotations

from pathlib import Path
from typing import Any

import click

try:
    import tomllib as toml
except ImportError:  # Python < 3.11
    import tomli as toml

from robocop import exceptions


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            return toml.load(tf)
    except (toml.TOMLDecodeError, OSError) as e:
        raise click.FileError(filename=str(config_path), hint=f"Error reading configuration file: {e}") from None


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


def extend_configs(config: dict[str, Any], config_path: Path, seen: set) -> dict[str, Any]:
    """Extend configuration files with the configs from the extends option."""
    if "extends" not in config:
        return config
    merged_config = {}
    for base_config in config["extends"]:
        if not isinstance(base_config, str):
            raise exceptions.ConfigurationError(
                f"Invalid 'extends' parameter value in the configuration file: '{config_path}'. "
                f"{base_config} is not a string."
            )
        if not base_config.endswith(".toml"):
            continue
        base_config = Path(base_config)
        if base_config.is_absolute():
            extended_path = base_config
        else:
            extended_path = (config_path.parent / base_config).resolve()
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


def get_relative_path(path: str | Path, parent_path: Path) -> Path:
    try:
        return Path(path).relative_to(parent_path)
    except ValueError:  # symlink etc
        return Path(path)


def get_common_parent_dirs(sources: list[Path]) -> list[Path]:
    """Return list of common parent directories for list of paths."""
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in sources]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )
    return [common_base, *common_base.parents]
