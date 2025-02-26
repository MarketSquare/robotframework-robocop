from __future__ import annotations

from collections.abc import Iterable, Iterator
from functools import lru_cache
from pathlib import Path
from re import Pattern
from typing import Any

import pathspec

try:
    import rich_click as click
except ImportError:
    import click

import tomli

DEFAULT_EXCLUDES = r"/(\.direnv|\.eggs|\.git|\.hg|\.nox|\.tox|\.venv|venv|\.svn)/"
INCLUDE_EXT = (".robot", ".resource")
DOTFILE_CONFIG = ".robotidy"
CONFIG_NAMES = ("robotidy.toml", "pyproject.toml", DOTFILE_CONFIG)


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


@lru_cache
def find_project_root(srcs: tuple[str, ...], ignore_git_dir: bool = False) -> Path:
    """
    Return a directory containing .git, or robotidy.toml.
    That directory will be a common parent of all files and directories
    passed in `srcs`.
    If no directory in the tree contains a marker that would specify it's the
    project root, the root of the file system is returned.
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


def load_toml_file(config_path: Path) -> dict[str, Any]:
    try:
        with config_path.open("rb") as tf:
            config = tomli.load(tf)
        return config
    except (tomli.TOMLDecodeError, OSError) as e:
        raise click.FileError(filename=str(config_path), hint=f"Error reading configuration file: {e}")


def read_pyproject_config(config_path: Path) -> dict[str, Any]:
    config = load_toml_file(config_path)
    if config_path.name != DOTFILE_CONFIG or "tool" in config:
        config = config.get("tool", {}).get("robotidy", {})
    return {k.replace("--", "").replace("-", "_"): v for k, v in config.items()}


@lru_cache
def get_gitignore(root: Path) -> pathspec.PathSpec:
    """Return a PathSpec matching gitignore content if present."""
    gitignore = root / ".gitignore"
    lines: list[str] = []
    if gitignore.is_file():
        with gitignore.open(encoding="utf-8") as gf:
            lines = gf.readlines()
    return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)


def should_parse_path(
    path: Path,
    root_parent: Path,
    exclude: Pattern[str] | None,
    extend_exclude: Pattern[str] | None,
    gitignore: pathspec.PathSpec | None,
) -> bool:
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
    if exclude and exclude.match(path.name):
        return False
    return True


def get_path_relative_to_project_root(path: Path, root_parent: Path) -> Path:
    try:
        return path.relative_to(root_parent)
    except ValueError:
        return path


def get_paths(src: tuple[str, ...], exclude: Pattern | None, extend_exclude: Pattern | None, skip_gitignore: bool):
    root = find_project_root(src)
    if skip_gitignore:
        gitignore = None
    else:
        gitignore = get_gitignore(root)
    sources = set()
    for s in src:
        if s == "-":
            sources.add("-")
            continue
        path = Path(s).resolve()
        root_parent = root.parent if root.parent else root
        if not should_parse_path(path, root_parent, exclude, extend_exclude, gitignore):
            continue
        if path.is_file():
            sources.add(path)
        elif path.is_dir():
            sources.update(iterate_dir((path,), exclude, extend_exclude, root_parent, gitignore))
        elif s == "-":
            sources.add(path)

    return sources


def iterate_dir(
    paths: Iterable[Path],
    exclude: Pattern | None,
    extend_exclude: Pattern | None,
    root_parent: Path,
    gitignore: pathspec.PathSpec | None,
) -> Iterator[Path]:
    for path in paths:
        if not should_parse_path(path, root_parent, exclude, extend_exclude, gitignore):
            continue
        if path.is_dir():
            yield from iterate_dir(
                path.iterdir(),
                exclude,
                extend_exclude,
                root_parent,
                gitignore + get_gitignore(path) if gitignore is not None else None,
            )
        elif path.is_file():
            yield path
