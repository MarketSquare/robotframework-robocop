from __future__ import annotations

import os
import stat
from functools import cache
from pathlib import Path

RESOLVED_PATHS_LIMIT = 100_000
_resolved_paths: dict[Path, Path] = {}


def get_relative_path(path: str | Path, parent_path: Path) -> Path:
    path = Path(path)
    relative = _relative_to(path, parent_path)
    return path if relative is None else relative


def _relative_to(path: Path, parent_path: Path) -> Path | None:
    """
    Return the path relative to the parent path, or None if the path is not inside the parent path.

    ``Path.relative_to`` is slow, so the common case where the path string starts with the parent path string is
    handled with string operations. ``Path.relative_to`` is used for the other cases (for example paths that differ
    only in the case on Windows).
    """
    path_str, parent_str = str(path), str(parent_path)
    if path_str.startswith(parent_str):
        rest = path_str[len(parent_str) :]
        if not rest:
            return Path()
        if parent_str.endswith(os.sep):  # root directory, such as / or C:\
            return Path(rest)
        if rest[0] == os.sep:
            return Path(rest[1:])
    try:
        return path.relative_to(parent_path)
    except ValueError:  # symlink etc
        return None


@cache
def _path_relative_to(path: Path, cwd: Path) -> Path:
    relative = _relative_to(path, cwd)
    return path if relative is None else relative


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
        resolved = _resolve_through_parent(path)
        _remember_resolved_path(path, resolved)
    return resolved


def _resolve_through_parent(path: Path) -> Path:
    """
    Resolve the path by joining its name with its resolved parent directory.

    Resolving a path is a filesystem call. Files from the same directory share the parent directory, so it is
    resolved only once. The path itself is resolved if it is a link (it may point outside its parent directory),
    if it does not exist or if it contains ``..``.

    Unlike ``Path.resolve``, the case of the file name is not normalized on case-insensitive file systems.
    """
    if not path.name or ".." in path.parts or _is_link_or_missing(path):
        return path.resolve()
    parent = path.absolute().parent
    resolved_parent = _resolved_paths.get(parent)
    if resolved_parent is None:
        resolved_parent = parent.resolve()
        _remember_resolved_path(parent, resolved_parent)
    return resolved_parent / path.name


def _is_link_or_missing(path: Path) -> bool:
    try:
        path_stat = os.lstat(path)
    except OSError:
        return True
    # junctions on Windows are not reported as symlinks
    is_reparse_point = getattr(path_stat, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
    return stat.S_ISLNK(path_stat.st_mode) or bool(is_reparse_point)


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
