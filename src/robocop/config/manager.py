from __future__ import annotations

import os
import stat
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pathspec

from robocop import exceptions, files
from robocop.cache import RobocopCache
from robocop.config.builder import ConfigBuilder
from robocop.config.parser import read_toml_config
from robocop.config.schema import Config, RawConfig
from robocop.source_file import SourceFile, build_source_file

if TYPE_CHECKING:
    from collections.abc import Generator, Sequence

CONFIG_NAMES = ("robocop.toml", "robot.toml", "pyproject.toml")
GitIgnorePathSpec = pathspec.GitIgnoreSpec
# File systems on Windows and macOS are case-insensitive by default, so file names from directory listings are
# compared case-insensitively to match the behaviour of ``Path.is_file()`` checks
CASE_INSENSITIVE_FS = sys.platform in ("win32", "darwin")


def _listing_key(name: str) -> str:
    return name.lower() if CASE_INSENSITIVE_FS else name


def _scan_directory(directory: Path) -> tuple[list[os.DirEntry[str]], dict[str, os.DirEntry[str]]]:
    """
    List directory entries.

    Entries returned by ``os.scandir`` hold the file type (and on Windows also the file stat) read together
    with the directory listing, which allows to avoid separate file system calls for each file.

    Returns:
        Tuple with the list of directory entries and the mapping of (normalized) entry names to entries.

    """
    with os.scandir(directory) as it:
        entries = list(it)
    return entries, {_listing_key(entry.name): entry for entry in entries}


def _is_link(entry: os.DirEntry[str]) -> bool:
    """Check if the entry is a symlink or other link (such as Windows junction) that may point outside its parent."""
    if entry.is_symlink():
        return True
    if os.name == "nt":
        # junctions are not reported by is_symlink(). The stat is cached with the entry, so it does not cost I/O
        attributes = getattr(entry.stat(follow_symlinks=False), "st_file_attributes", 0)
        return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)
    return False


def _entry_is_dir(entries: dict[str, os.DirEntry[str]], name: str) -> bool:
    entry = entries.get(name)
    return entry is not None and entry.is_dir()


def _entry_is_file(entries: dict[str, os.DirEntry[str]], name: str) -> bool:
    entry = entries.get(name)
    return entry is not None and entry.is_file()


class GitIgnoreResolver:
    def __init__(self) -> None:
        self.cached_ignores: dict[Path, tuple[Path, GitIgnorePathSpec]] = {}
        self.ignore_dirs: set[Path] = set()

    def path_excluded(self, path: Path, gitignores: list[tuple[Path, GitIgnorePathSpec]]) -> bool:
        """Find path gitignores and check if file is excluded."""
        if not gitignores:
            return False
        is_dir = path.is_dir()
        for gitignore_path, gitignore in gitignores:
            relative_path = files.get_relative_path(path, gitignore_path)
            path_str = str(relative_path)
            # fixes a bug in pathspec where directory needs to end with / to be ignored by pattern
            if is_dir and path_str != ".":
                path_str = f"{path_str}{os.sep}"
            if gitignore.match_file(path_str):
                return True
        return False

    def read_gitignore(self, path: Path) -> GitIgnorePathSpec:
        """Return a PathSpec loaded from the file."""
        with path.open(encoding="utf-8") as gf:
            lines = gf.readlines()
        return pathspec.GitIgnoreSpec.from_lines(lines)

    def resolve_path_ignores(self, path: Path) -> list[tuple[Path, GitIgnorePathSpec]]:
        """
        Visit all parent directories and find all gitignores.

        Gitignores are cached for multiple sources.

        Args:
            path: path to file/directory

        Returns:
            PathSpec from merged gitignores.

        """
        # TODO: respect nogitignore flag
        if path.is_file():
            path = path.parent
        gitignores: list[tuple[Path, GitIgnorePathSpec]] = []
        search_paths = (parent for parent in [path, *path.parents])
        for parent_path in search_paths:
            if parent_path in self.ignore_dirs:  # dir that does not have .gitignore (marked as such)
                gitignores.extend([self.cached_ignores[path] for path in search_paths if path in self.cached_ignores])
                break
            if parent_path in self.cached_ignores:
                gitignores.append(self.cached_ignores[parent_path])
                # if any parent is cached, we can retrieve any parent with gitignore from cache and return early
                gitignores.extend([self.cached_ignores[path] for path in search_paths if path in self.cached_ignores])
                break
            if (gitignore_path := parent_path / ".gitignore").is_file():
                gitignore = self.read_gitignore(gitignore_path)
                self.cached_ignores[parent_path] = (parent_path, gitignore)
                gitignores.append((parent_path, gitignore))
            else:
                self.ignore_dirs.add(parent_path)
            if (parent_path / ".git").is_dir():
                break
        return gitignores

    def get_directory_ignores(
        self,
        directory: Path,
        entries: dict[str, os.DirEntry[str]],
        parent_ignores: list[tuple[Path, GitIgnorePathSpec]],
    ) -> list[tuple[Path, GitIgnorePathSpec]]:
        """
        Return gitignores that apply to the directory content, reusing gitignores already found for its parent.

        It is the equivalent of ``resolve_path_ignores``, but it does not need to visit parent directories nor to
        access the file system for checking if the files exist - it uses the directory listing instead.

        Args:
            directory: resolved path to the directory
            entries: directory listing (see ``_scan_directory``)
            parent_ignores: gitignores that apply to the parent directory

        Returns:
            List of gitignores from the directory and its parents.

        """
        gitignores: list[tuple[Path, GitIgnorePathSpec]] = []
        if directory in self.cached_ignores:
            gitignores.append(self.cached_ignores[directory])
        elif directory not in self.ignore_dirs:
            if _entry_is_file(entries, ".gitignore"):
                gitignore = self.read_gitignore(Path(entries[".gitignore"].path))
                self.cached_ignores[directory] = (directory, gitignore)
                gitignores.append((directory, gitignore))
            else:
                self.ignore_dirs.add(directory)
        if _entry_is_dir(entries, ".git"):  # do not look for gitignores outside the repository
            return gitignores
        return gitignores + parent_ignores

    @staticmethod
    def relative_ignores(
        directory: Path, gitignores: list[tuple[Path, GitIgnorePathSpec]]
    ) -> list[tuple[str, GitIgnorePathSpec]]:
        """
        Return the directory path relative to each gitignore location.

        Paths of the files from the directory can be then matched against gitignores by simple string concatenation.

        Returns:
            List of tuples with the relative directory path prefix (ending with separator) and the gitignore.

        """
        relative_ignores = []
        for gitignore_path, gitignore in gitignores:
            relative_path = str(files.get_relative_path(directory, gitignore_path))
            prefix = "" if relative_path == "." else f"{relative_path}{os.sep}"
            relative_ignores.append((prefix, gitignore))
        return relative_ignores

    @staticmethod
    def entry_excluded(relative_ignores: list[tuple[str, GitIgnorePathSpec]], name: str, is_dir: bool) -> bool:
        """Check if directory entry is excluded by any of the gitignores (see ``relative_ignores``)."""
        suffix = os.sep if is_dir else ""
        return any(gitignore.match_file(f"{prefix}{name}{suffix}") for prefix, gitignore in relative_ignores)


class ConfigManager:
    """
    Finds and loads configuration files for each file.

    Config provided from cli takes priority. ``--config`` option overrides any found configuration file.
    """

    def __init__(
        self,
        sources: list[str] | None = None,
        config: Path | None = None,
        root: Path | None = None,
        ignore_git_dir: bool = False,
        ignore_file_config: bool = False,
        skip_gitignore: bool = False,
        force_exclude: bool = False,
        overwrite_config: RawConfig | None = None,
    ) -> None:
        """
        Initialize ConfigManager.

        Args:
            sources: List of sources with Robot Framework files.
            config: Path to configuration file.
            root: Root of the project. Can be supplied if it's known beforehand (for example by IDE plugin)
            Otherwise it will be automatically found.
            ignore_git_dir: Flag for project root discovery to decide if directories with `.git` should be ignored.
            ignore_file_config: If set to True, Robocop will not load found configuration files
            skip_gitignore: Do not load .gitignore files when looking for the files to parse
            force_exclude: Enforce exclusions, even for paths passed directly in the command-line
            overwrite_config: Overwrite existing configuration file with the Config class

        """
        self.config_builder = ConfigBuilder()
        self.cached_configs: dict[Path, Config] = {}
        self.overwrite_config = overwrite_config
        self.ignore_git_dir = ignore_git_dir
        self.ignore_file_config = ignore_file_config
        self.skip_gitignore = skip_gitignore
        self.gitignore_resolver = GitIgnoreResolver()
        self.overridden_config = config is not None
        self.root = root or Path.cwd()
        self.default_config: Config = self.get_default_config(config, sources)
        self.sources = sources if sources else self.default_config.sources
        # ignore file filters on paths passed directly
        self.ignore_file_filters = not (force_exclude or self.default_config.force_exclude) and bool(sources)
        self._paths: dict[Path, SourceFile] = {}
        self._project_paths: dict[Path, SourceFile] | None = None
        self.resolved_paths = False
        self._cache: RobocopCache | None = None

    @property
    def cache(self) -> RobocopCache:
        """Get the file cache, initializing it lazily if needed."""
        if self._cache is None:
            cache_config = self.default_config.cache
            self._cache = RobocopCache(
                cache_dir=cache_config.cache_dir,
                enabled=cache_config.enabled,
                verbose=self.default_config.verbose,
            )
        return self._cache

    @property
    def paths(self) -> Generator[SourceFile, None, None]:
        # TODO: what if we provide the same path twice - tests
        if not self.resolved_paths:
            self.resolve_paths(self.sources, ignore_file_filters=self.ignore_file_filters)
        yield from self._paths.values()

    @property
    def project_paths(self) -> Generator[SourceFile, None, None]:
        """
        All source files in the project, even if only selected paths are linted.

        Project level checks need to know the whole project - for example a keyword defined in the linted file
        can be used by a file outside the linted paths. Source files that were already resolved are reused, so
        their models are only parsed once.
        """
        if self._project_paths is None:
            self._project_paths = {}
            self.resolve_paths([self.root], target=self._project_paths)
        yield from self._project_paths.values()

    def get_default_config(self, config_path: Path | None, sources: list[str] | None) -> Config:
        """Get the default config either from --config option or from the cli."""
        if config_path:
            configuration = read_toml_config(config_path)
            if configuration is not None:  # TODO: should raise
                config_file_raw = RawConfig.from_dict(configuration, config_path.resolve())
                return self.config_builder.from_raw(self.overwrite_config, config_file_raw)
        if not self.ignore_file_config:
            if sources:
                sources_paths: list[Path] = [Path(path) for path in sources]
                paths = [path.resolve() for path in sources_paths if not path.is_symlink()]
            else:
                paths = [Path.cwd().resolve()]
            directories = files.get_common_parent_dirs(paths)
            return self.find_config_in_dirs(directories, default=None)
        return self.config_builder.from_raw(self.overwrite_config, None)

    def is_git_project_root(self, path: Path, entries: dict[str, os.DirEntry[str]] | None = None) -> bool:
        """Check if current directory contains .git directory and might be a project root."""
        if self.ignore_git_dir:
            return False
        if entries is not None:
            return _entry_is_dir(entries, ".git")
        return (path / ".git").is_dir()

    def find_config_in_directory(
        self, directory: Path, entries: dict[str, os.DirEntry[str]] | None = None
    ) -> Config | None:
        """
        Search for a configuration file in the specified directory.

        This method iterates through predefined configuration filenames and attempts
        to locate and load the first matching configuration file found in the given
        directory. Only configuration files with valid Robocop entry are taken into account.

        Args:
            directory: The directory path to search for configuration files.
            entries: Optional directory listing. If provided, it is used instead of checking each file separately.

        Returns:
            A Config object if a configuration file is found and successfully
            loaded, otherwise None.

        """
        for config_filename in CONFIG_NAMES:
            if entries is not None:
                if not _entry_is_file(entries, config_filename):
                    continue
                config_path = directory / entries[config_filename].name
            elif not (config_path := (directory / config_filename)).is_file():
                continue
            if configuration := read_toml_config(config_path):
                config_file_raw = RawConfig.from_dict(configuration, config_path)
                return self.config_builder.from_raw(self.overwrite_config, config_file_raw)
        return None

    def find_config_in_dirs(self, directories: list[Path] | Sequence[Path], default: Config | None) -> Config:
        seen: list[Path] = []  # if we find config, mark all visited directories with resolved config
        found = default
        for check_dir in directories:
            if check_dir in self.cached_configs:
                found = self.cached_configs[check_dir]
                break
            seen.append(check_dir)
            if (directory_config := self.find_config_in_directory(check_dir)) is not None:
                found = directory_config
                break
            if self.is_git_project_root(check_dir):
                break

        if found is None:
            found = self.config_builder.from_raw(self.overwrite_config, None)
        self.cached_configs.update(dict.fromkeys(seen, found))
        return found

    def get_config_for_source_file(self, source_file: Path) -> Config:
        """
        Find the closest config to the source file or directory.

        If it was loaded before, it will be returned from the cache. Otherwise, we will
        load it and save it to the cache first.

        Args:
            source_file: Path to Robot Framework source file or directory.

        """
        if self.overridden_config or self.ignore_file_config:
            return self.default_config
        return self.find_config_in_dirs(source_file.parents, self.default_config)

    def get_config_for_directory_content(self, directory: Path, entries: dict[str, os.DirEntry[str]]) -> Config:
        """
        Find the closest config for the files inside the directory.

        It is the equivalent of ``get_config_for_source_file`` called for any file in the directory, but it uses
        the directory listing instead of checking each configuration file name separately.

        Args:
            directory: resolved path to the directory
            entries: directory listing (see ``_scan_directory``)

        """
        if self.overridden_config or self.ignore_file_config:
            return self.default_config
        if directory in self.cached_configs:
            return self.cached_configs[directory]
        config = self.find_config_in_directory(directory, entries)
        if config is None:
            if self.is_git_project_root(directory, entries):
                config = self.default_config
            else:
                config = self.find_config_in_dirs(directory.parents, self.default_config)
        self.cached_configs[directory] = config
        return config

    def resolve_paths(
        self,
        sources: list[Path] | list[str],
        ignore_file_filters: bool = False,
        target: dict[Path, SourceFile] | None = None,
    ) -> None:
        """
        Find all files to parse and their corresponding configs.

        Initially, sources can be ["."] (if not path provided, assume the current working directory).
        It can be also any list of paths, for example ["tests/", "file.robot"].

        Args:
            sources: list of sources from CLI or configuration file.
            ignore_file_filters: force robocop to parse file even if it's excluded in the configuration
            target: where the resolved source files are stored. Defaults to the linted paths.

        """
        if target is None:
            target = self._paths
        config: Config | None = None
        for source in sources:
            source_not_resolved = Path(source)
            source = source_not_resolved.resolve()
            if source in target:
                continue
            if not source.exists():
                if source_not_resolved.is_symlink():  # i.e. dangling symlink
                    continue
                raise exceptions.FatalError(f"File '{source}' does not exist")
            config = self.get_config_for_source_file(source)
            if not ignore_file_filters:
                if config.file_filters.path_excluded(source_not_resolved):
                    continue
                if source.is_file() and not config.file_filters.path_included(source_not_resolved):
                    continue
                if not self.skip_gitignore:
                    source_absolute = Path(os.path.abspath(source_not_resolved))
                    source_gitignore = self.gitignore_resolver.resolve_path_ignores(source_absolute)
                    if self.gitignore_resolver.path_excluded(source_absolute, source_gitignore):
                        continue
            if source.is_dir():
                gitignores = [] if self.skip_gitignore else self.gitignore_resolver.resolve_path_ignores(source)
                self._walk_directory(source, _scan_directory(source), gitignores, target)
            elif source.is_file():
                self._add_source_file(source, config, target)

    def _add_source_file(self, path: Path, config: Config, target: dict[Path, SourceFile]) -> None:
        """Add the source file to the target. The path must be already resolved."""
        source_file = self._paths.get(path)
        if source_file is None:
            files.mark_resolved(path)
            source_file = build_source_file(path, config)
        target[path] = source_file

    def _walk_directory(
        self,
        directory: Path,
        listing: tuple[list[os.DirEntry[str]], dict[str, os.DirEntry[str]]],
        gitignores: list[tuple[Path, GitIgnorePathSpec]],
        target: dict[Path, SourceFile],
    ) -> None:
        """
        Recursively find all files to parse in the directory.

        It is the equivalent of calling ``resolve_paths`` on each directory entry, but it is optimized for
        processing a large number of files. Directory listings are used to check file types and to find
        configuration and gitignore files, and the configuration and gitignores are resolved once per directory
        instead of once per file. Since the directory path is resolved, the paths of its entries are resolved
        too, unless they are links - which are handled by ``resolve_paths``.

        Args:
            directory: resolved path to the directory
            listing: directory listing (see ``_scan_directory``)
            gitignores: gitignores that apply to the directory content (including the directory own gitignore)
            target: where the resolved source files are stored

        """
        entries, entries_by_name = listing
        config = self.get_config_for_directory_content(directory, entries_by_name)
        relative_ignores = self.gitignore_resolver.relative_ignores(directory, gitignores)
        for entry in entries:
            if _is_link(entry):
                self.resolve_paths([entry.path], target=target)
                continue
            path = Path(entry.path)
            if path in target or config.file_filters.path_excluded(path):
                continue
            if entry.is_dir():
                sub_listing = _scan_directory(path)
                sub_gitignores = self._get_subdirectory_ignores(path, sub_listing[1], gitignores)
                if self._subdirectory_excluded(path, entry.name, sub_listing[1], sub_gitignores, relative_ignores):
                    continue
                self._walk_directory(path, sub_listing, sub_gitignores, target)
            elif entry.is_file():
                if not config.file_filters.path_included(path):
                    continue
                if self.gitignore_resolver.entry_excluded(relative_ignores, entry.name, is_dir=False):
                    continue
                self._add_source_file(path, config, target)

    def _get_subdirectory_ignores(
        self,
        directory: Path,
        entries: dict[str, os.DirEntry[str]],
        parent_gitignores: list[tuple[Path, GitIgnorePathSpec]],
    ) -> list[tuple[Path, GitIgnorePathSpec]]:
        if self.skip_gitignore:
            return []
        return self.gitignore_resolver.get_directory_ignores(directory, entries, parent_gitignores)

    def _subdirectory_excluded(
        self,
        directory: Path,
        name: str,
        entries: dict[str, os.DirEntry[str]],
        gitignores: list[tuple[Path, GitIgnorePathSpec]],
        parent_relative_ignores: list[tuple[str, GitIgnorePathSpec]],
    ) -> bool:
        """
        Check if the subdirectory is excluded by gitignores.

        The directory is matched against its own gitignore (as ``.``) and, unless it is the root of other git
        repository, against the gitignores of its parent.
        """
        if self.skip_gitignore:
            return False
        if gitignores and gitignores[0][0] == directory and gitignores[0][1].match_file("."):
            return True
        if _entry_is_dir(entries, ".git"):
            return False
        return self.gitignore_resolver.entry_excluded(parent_relative_ignores, name, is_dir=True)
