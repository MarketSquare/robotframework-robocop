from __future__ import annotations

from typing import TYPE_CHECKING, Any

import click

if TYPE_CHECKING:
    from pathlib import Path

try:
    import tomllib as toml
except ImportError:  # Python < 3.11
    import tomli as toml


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            return toml.load(tf)
    except (toml.TOMLDecodeError, OSError) as e:
        raise click.FileError(
            filename=str(config_path), hint=f"Error reading configuration file: {e}"
        ) from None  # TODO: check typer errors


def read_toml_config(config_path: Path) -> dict[str, Any] | None:
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
        return None
    return {k.replace("-", "_"): v for k, v in config.items()}


def get_path_relative_to_path(path: Path, root_parent: Path) -> Path:
    try:
        return path.relative_to(root_parent)
    except ValueError:
        return path
