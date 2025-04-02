from __future__ import annotations

from pathlib import Path
from typing import Any

import click

try:
    import tomllib as toml
except ImportError:  # Python < 3.11
    import tomli as toml


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            return toml.load(tf)
    except (toml.TOMLDecodeError, OSError) as e:
        raise click.FileError(filename=str(config_path), hint=f"Error reading configuration file: {e}") from None


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


def get_relative_path(path: str | Path, parent_path: Path) -> Path:
    try:
        return Path(path).relative_to(parent_path)
    except ValueError:  # symlink etc
        return path


def get_common_parent_dirs(sources: list[Path]) -> list[Path]:
    """Return list of common parent directories for list of paths."""
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in sources]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )
    return [common_base, *common_base.parents]
