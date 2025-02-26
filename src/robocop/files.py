from __future__ import annotations

from collections.abc import Iterable, Iterator
from functools import lru_cache
from pathlib import Path
from re import Pattern
from typing import Any

import click
import pathspec

try:
    import tomli as toml
except ImportError:  # from Python 3.11
    import toml


CONFIG_NAMES = frozenset(("robotidy.toml", "pyproject.toml"))
INCLUDE_EXT = (".robot", ".resource")


def find_project_root(srcs: tuple[str, ...] | None, ignore_git_dir: bool) -> Path:
    """
    Find and return the root of the project root.

    Project root is determined by existence of the `.git` directory (if `ignore_git_dir` is `False`) or by
    existence of configuration file. If nothing is found, the root of the file system is returned.

    Args:
        srcs: list of source paths.
        ignore_git_dir: whether to ignore existence of `.git` directory.

    Returns:
        path of the project root.

    """
    if not srcs:
        return Path("/").resolve()
    path_srcs = [Path(Path.cwd(), src).resolve() for src in srcs]
    # A list of lists of parents for each 'src'. 'src' is included as a
    # "parent" of itself if it is a directory
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in path_srcs]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )

    for directory in (common_base, *common_base.parents):
        if not ignore_git_dir and (directory / ".git").exists():
            return directory
        if any((directory / config_name).is_file() for config_name in CONFIG_NAMES):
            return directory
    return directory


def get_config_path(directory: Path) -> Path | None:
    """Return path to configuration file if the configuration file exists."""
    for name in CONFIG_NAMES:
        if (config_path := (directory / name)).is_file():
            return config_path
    return None


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            return toml.load(tf)
    except (toml.TOMLDecodeError, OSError) as e:
        raise click.FileError(
            filename=str(config_path), hint=f"Error reading configuration file: {e}"
        ) from None  # TODO: check typer errors


def read_toml_config(config_path: Path) -> dict[str, Any]:
    """
    Load and return toml configuration file.

    For pyproject.toml files we need to retrieve configuration from [tool.robocop] section. This section is not
    required for the robocop.toml file.
    """
    config = load_toml_file(config_path)
    if config_path.name == "pyproject.toml" or "tool" in config:
        config = config.get("tool", {}).get("robotidy", {})
    return {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}


@lru_cache
def find_source_config_file(src: Path, ignore_git_dir: bool = False) -> Path | None:
    """
    Find and return configuration file for the source path.

    This method looks iteratively in source parents for directory that contains configuration file and
    returns its path. The lru_cache speeds up searching if there are multiple files in the same directory (they will
    have the same configuration file).

    If ``.git`` directory is found and ``ignore_git_dir`` is set to ``False``, or top directory is reached, this method
    returns ``None``.
    """
    if src.is_dir():
        if not ignore_git_dir and src.name == ".git":
            return None
        for config_filename in CONFIG_NAMES:
            if (src / config_filename).is_file():
                return src / config_filename
        if not src.parents:
            return None
    return find_source_config_file(src.parent, ignore_git_dir)


def get_path_relative_to_project_root(path: Path, root_parent: Path) -> Path:
    try:
        return path.relative_to(root_parent)
    except ValueError:
        return path


def should_parse_path(
    path: Path,
    overridden_sources: set[Path],
    root_parent: Path,
    exclude: Pattern[str] | None,
    extend_exclude: Pattern[str] | None,
    gitignore: pathspec.PathSpec | None,
) -> bool:
    """
    Decide if source path should be parsed.

    Args:
        path: Source path.
        overridden_sources: Source paths that should always be parsed.
        root_parent: Parent of root of the project.
        exclude: Pattern of default paths to be excluded.
        extend_exclude: Pattern for paths that should be excluded on top of default ones.
        gitignore: Parsed gitignore file.

    Returns:
        Boolean value whether source path should be parsed.

    """
    if path.is_file() and path in overridden_sources:
        return True
    normalized_path = str(path)
    for pattern in (exclude, extend_exclude):
        match = pattern.search(normalized_path) if pattern else None
        if bool(match and match.group(0)):
            return False
    if gitignore is not None:
        relative_path = get_path_relative_to_project_root(path, root_parent)
        if gitignore.match_file(relative_path):
            return False
    if path.is_file():
        return path.suffix in INCLUDE_EXT
    return not (exclude and exclude.match(path.name))


@lru_cache
def get_gitignore(root: Path) -> pathspec.PathSpec:
    """Return a PathSpec matching gitignore content if present."""
    gitignore = root / ".gitignore"
    lines: list[str] = []
    if gitignore.is_file():
        with gitignore.open(encoding="utf-8") as gf:
            lines = gf.readlines()
    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)


def iterate_dir(
    paths: Iterable[Path],
    overridden_sources: set[Path],
    exclude: Pattern | None,
    extend_exclude: Pattern | None,
    root_parent: Path,
    gitignore: pathspec.PathSpec | None,
) -> Iterator[Path]:
    for path in paths:
        if not should_parse_path(path, overridden_sources, root_parent, exclude, extend_exclude, gitignore):
            continue
        if path.is_dir():
            yield from iterate_dir(
                path.iterdir(),
                overridden_sources,
                exclude,
                extend_exclude,
                root_parent,
                gitignore + get_gitignore(path) if gitignore is not None else None,
            )
        elif path.is_file():
            yield path
