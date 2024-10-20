from functools import lru_cache
from pathlib import Path

from pathspec import PathSpec

from robocop.exceptions import FileError

DEFAULT_EXCLUDES = r"(\.direnv|\.eggs|\.git|\.hg|\.nox|\.tox|\.venv|venv|\.svn)"


def find_project_root(root, srcs):
    """
    Find project root.
    If not provided in ``root`` argument, the first parent directory containing either .git, .robocop or pyproject.toml
    file in any of  ``srcs`` paths will be root category.
    If not found, returns the root of the file system.
    """
    if root is not None:
        return Path(root)
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
        if (
            (directory / ".git").exists()
            or (directory / "pyproject.toml").is_file()
            or (directory / ".robocop").is_file()
        ):
            return directory
    return directory


def find_file_in_project_root(config_name, root, ignore_git_dir: bool):
    for parent in (root, *root.parents):
        if (parent / config_name).is_file():
            return parent / config_name
        if not ignore_git_dir and (parent / ".git").exists():
            return None


@lru_cache
def get_gitignore(root):
    """Return a PathSpec matching gitignore content if present."""
    gitignore = root / ".gitignore"
    lines = []
    if gitignore.is_file():
        with gitignore.open(encoding="utf-8") as gf:
            lines = gf.readlines()
    return PathSpec.from_lines("gitwildmatch", lines)


def get_files(config):
    gitignore = get_gitignore(config.root)
    for file in config.paths:
        yield from get_absolute_path(Path(file), config, gitignore)


def get_absolute_path(path, config, gitignore):
    if not path.exists():
        raise FileError(path)
    if config.is_path_ignored(path):
        return
    if gitignore is not None and gitignore.match_file(path):
        return
    if path.is_file():
        if should_parse(config, path):
            yield path.absolute()
    elif path.is_dir():
        for file in path.iterdir():
            if file.is_dir() and not config.recursive:
                continue
            yield from get_absolute_path(
                file,
                config,
                gitignore + get_gitignore(path) if gitignore is not None else None,
            )


def should_parse(config, file):
    """Check if file extension is in list of supported file types (can be configured from cli)"""
    return file.suffix and file.suffix.lower() in config.filetypes
