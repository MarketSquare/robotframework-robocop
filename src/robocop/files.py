from __future__ import annotations

from functools import cache
from pathlib import Path


def get_relative_path(path: str | Path, parent_path: Path) -> Path:
    try:
        return Path(path).relative_to(parent_path)
    except ValueError:  # symlink etc
        return Path(path)


@cache
def path_relative_to_cwd(path: Path) -> Path:
    """Return path in relation to cwd path. Results are cached."""
    cwd = Path.cwd()  # TODO: potentially performance heavy - check
    try:
        return path.relative_to(cwd)
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
