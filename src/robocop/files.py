from __future__ import annotations

from functools import cache
from pathlib import Path

RESOLVED_PATHS_LIMIT = 100_000
_resolved_paths: dict[Path, Path] = {}


def get_relative_path(path: str | Path, parent_path: Path) -> Path:
    try:
        return Path(path).relative_to(parent_path)
    except ValueError:  # symlink etc
        return Path(path)


@cache
def _path_relative_to(path: Path, cwd: Path) -> Path:
    try:
        return path.relative_to(cwd)
    except ValueError:  # symlink etc
        return path


def path_relative_to_cwd(path: Path) -> Path:
    """Return path in relation to cwd path. Results are cached per working directory."""
    return _path_relative_to(path, Path.cwd())


def resolve_path(path: Path) -> Path:
    """
    Return the resolved (absolute, symlink free) path.

    ``Path.resolve`` is a filesystem call and it is used all over the project analysis to normalize paths before
    comparing them or using them as dictionary keys. A project contains a limited number of paths, but they are
    resolved hundreds of thousands of times, so the results are cached. The cache is bounded, so that it does not
    grow without a limit in long living processes such as the MCP server.

    Returns:
        Resolved path.

    """
    resolved = _resolved_paths.get(path)
    if resolved is None:
        resolved = path.resolve()
        _remember_resolved_path(path, resolved)
    return resolved


def mark_resolved(path: Path, resolved: Path | None = None) -> None:
    """
    Mark the path as already resolved, so it is not resolved again by ``resolve_path``.

    It allows to skip the costly ``Path.resolve`` call for paths that are known to be resolved, for example paths
    found when walking the resolved directory, or paths resolved in another process.
    """
    _remember_resolved_path(path, path if resolved is None else resolved)


def _remember_resolved_path(path: Path, resolved: Path) -> None:
    if len(_resolved_paths) >= RESOLVED_PATHS_LIMIT:
        _resolved_paths.clear()
    _resolved_paths[path] = resolved


def get_common_parent_dirs(sources: list[Path]) -> list[Path]:
    """Return list of common parent directories for list of paths."""
    src_parents = [list(path.parents) + ([path] if path.is_dir() else []) for path in sources]

    common_base = max(
        set.intersection(*(set(parents) for parents in src_parents)),
        key=lambda path: path.parts,
    )
    return [common_base, *common_base.parents]
