from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

import pathspec

from robocop import exceptions, files
from robocop.cache import RobocopCache
from robocop.config import Config
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from collections.abc import Generator

CONFIG_NAMES = frozenset(("robocop.toml", "pyproject.toml", "robot.toml"))


class GitIgnoreResolver:
    def __init__(self):
        self.cached_ignores: dict[Path, list[pathspec.PathSpec] | None] = {}
        self.ignore_dirs: set[Path] = set()

    def path_excluded(self, path: Path, gitignores: list[tuple[Path, pathspec.PathSpec]]) -> bool:
        """Find path gitignores and check if file is excluded."""
        if not gitignores:
            return False
        for gitignore_path, gitignore in gitignores:
            relative_path = files.get_relative_path(path, gitignore_path)
            path = str(relative_path)
            # fixes a bug in pathspec where directory needs to end with / to be ignored by pattern
            if relative_path.is_dir() and path != ".":
                path = f"{path}{os.sep}"
            if gitignore.match_file(path):
                return True
        return False

    def read_gitignore(self, path: Path) -> pathspec.PathSpec:
        """Return a PathSpec loaded from the file."""
        with path.open(encoding="utf-8") as gf:
            lines = gf.readlines()
        return pathspec.PathSpec.from_lines(pathspec.patterns.GitWildMatchPattern, lines)

    def resolve_path_ignores(self, path: Path) -> list[tuple[Path, pathspec.PathSpec]]:
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
        gitignores = []
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


class ConfigManager:
    """
    Finds and loads configuration files for each file.

    Config provided from cli takes priority. ``--config`` option overrides any found configuration file.
    """

    def __init__(
        self,
        sources: list[str] | None = None,
        config: Path | None = None,
        root: str | None = None,
        ignore_git_dir: bool = False,
        ignore_file_config: bool = False,
        skip_gitignore: bool = False,
        force_exclude: bool = False,
        overwrite_config: Config | None = None,
    ):
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
        self.cached_configs: dict[Path, Config] = {}
        self.overwrite_config = overwrite_config
        self.ignore_git_dir = ignore_git_dir
        self.ignore_file_config = ignore_file_config
        self.force_exclude = force_exclude
        self.skip_gitignore = skip_gitignore
        self.gitignore_resolver = GitIgnoreResolver()
        self.overridden_config = (
            config is not None
        )  # TODO: what if both cli and --config? should take --config then apply cli
        self.root = root or Path.cwd()
        self.sources = sources
        self.default_config: Config = self.get_default_config(config)
        self._paths: dict[Path, SourceFile] | None = None
        self._cache: RobocopCache | None = None

    @property
    def cache(self) -> RobocopCache:
        """Get the file cache, initializing it lazily if needed."""
        if self._cache is None:
            cache_config = self.default_config.cache
            self._cache = RobocopCache(
                cache_dir=cache_config.cache_dir if cache_config else None,
                enabled=cache_config.enabled if cache_config else True,
                verbose=self.default_config.verbose or False,
            )
        return self._cache

    @property
    def paths(self) -> Generator[SourceFile, None, None]:
        # TODO: what if we provide the same path twice - tests
        if self._paths is None:
            self._paths = {}
            sources = self.sources if self.sources else self.default_config.sources
            ignore_file_filters = not self.force_exclude and bool(sources)
            self.resolve_paths(sources, ignore_file_filters=ignore_file_filters)
        yield from self._paths.values()

    def get_default_config(self, config_path: Path | None) -> Config:
        """Get default config either from --config option or from the cli."""
        if config_path:
            configuration = files.read_toml_config(config_path)
            config = Config.from_toml(configuration, config_path.resolve())
        elif not self.ignore_file_config:
            sources = [Path(path).resolve() for path in self.sources] if self.sources else [Path.cwd()]
            directories = files.get_common_parent_dirs(sources)
            config = self.find_config_in_dirs(directories, default=None)
            if not config:
                config = Config()
                self.cached_configs.update(dict.fromkeys(directories, config))
        else:
            config = Config()
        config.overwrite_from_config(self.overwrite_config)
        return config

    def is_git_project_root(self, path: Path) -> bool:
        """Check if current directory contains .git directory and might be a project root."""
        if self.ignore_git_dir:
            return False
        return (path / ".git").is_dir()

    def find_closest_config(self, source: Path, default: Config | None) -> Config:
        """Look in the directory and its parents for the closest valid configuration file."""
        return self.find_config_in_dirs(source.parents, default)

    def find_config_in_dirs(self, directories: list[Path], default: Config | None) -> Config:
        seen = []  # if we find config, mark all visited directories with resolved config
        for check_dir in directories:
            if check_dir in self.cached_configs:
                return self.cached_configs[check_dir]
            seen.append(check_dir)
            for config_filename in CONFIG_NAMES:
                if (config_path := (check_dir / config_filename)).is_file():
                    configuration = files.read_toml_config(config_path)
                    if configuration:
                        config = Config.from_toml(configuration, config_path)
                        config.overwrite_from_config(self.overwrite_config)  # TODO those two lines together
                        self.cached_configs.update(dict.fromkeys(seen, config))
                        if config.verbose:
                            print(f"Loaded {config_path} configuration file.")
                        return config
            if self.is_git_project_root(check_dir):
                break

        if default:
            self.cached_configs.update(dict.fromkeys(seen, default))
        return default

    def get_config_for_source_file(self, source_file: Path) -> Config:
        """
        Find the closest config to the source file or directory.

        If it was loaded before it will be returned from the cache. Otherwise, we will load it and save it to cache
        first.

        Args:
            source_file: Path to Robot Framework source file or directory.

        """
        if self.overridden_config or self.ignore_file_config:
            return self.default_config
        return self.find_closest_config(source_file, self.default_config)

    def resolve_paths(
        self,
        sources: list[str | Path],
        ignore_file_filters: bool = False,
    ) -> None:
        """
        Find all files to parse and their corresponding configs.

        Initially sources can be ["."] (if not path provided, assume current working directory).
        It can be also any list of paths, for example ["tests/", "file.robot"].

        Args:
            sources: list of sources from CLI or configuration file.
            gitignores: list of gitignore pathspec and their locations for path resolution.
            ignore_file_filters: force robocop to parse file even if it's excluded in the configuration

        """
        source_gitignore = None
        config = None
        for source in sources:
            source_not_resolved = Path(source)
            source = source_not_resolved.resolve()
            if source in self._paths:
                continue
            if not source.exists():
                if source_not_resolved.is_symlink():  # i.e. dangling symlink
                    continue
                raise exceptions.FatalError(f"File '{source}' does not exist")
            if config is None:  # first file in the directory
                config = self.get_config_for_source_file(source)
            if not ignore_file_filters:
                if config.file_filters.path_excluded(source_not_resolved):
                    continue
                if source.is_file() and not config.file_filters.path_included(source_not_resolved):
                    continue
                if not self.skip_gitignore:
                    source_gitignore = self.gitignore_resolver.resolve_path_ignores(source_not_resolved)
                    if self.gitignore_resolver.path_excluded(source_not_resolved, source_gitignore):
                        continue
            if source.is_dir():
                self.resolve_paths(source.iterdir())
            elif source.is_file():
                self._paths[source] = SourceFile(path=source, config=config)
