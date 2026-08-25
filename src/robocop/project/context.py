"""
Project wide context shared between project level checkers.

The context is built once per run, before any project checker is executed. It contains parsed models of all source
files in the project together with keyword definitions, keyword usages, variables and resolved imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
from typing import TYPE_CHECKING

from robot.errors import DataError

from robocop.files import resolve_path
from robocop.linter.utils.misc import normalize_robot_name
from robocop.project.collector import ProjectFileCollector
from robocop.project.definitions import ImportStatus, ImportType, KeywordDefinition
from robocop.project.imports import ImportResolver, build_search_paths
from robocop.project.libraries import LibraryRequest, build_library_loader
from robocop.project.serialization import collected_file_from_dict, collected_file_to_dict
from robocop.project.variables import VariableScope
from robocop.version_handling import ROBOT_VERSION

BUILTIN_LIBRARY = LibraryRequest(name="BuiltIn")
"""BuiltIn library is always available, without being imported."""

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from robot.api import Languages  # RF 6.0

    from robocop.cache import RobocopCache
    from robocop.config.manager import ConfigManager
    from robocop.project.collector import CollectedFile
    from robocop.project.definitions import KeywordUsage, ResolvedImport, VariableDefinition
    from robocop.project.libraries import LibraryLoader
    from robocop.source_file import SourceFile


@dataclass
class ProjectFile:
    """Single source file in the project together with everything collected from it."""

    source_file: SourceFile
    collected: CollectedFile
    imports: list[ResolvedImport] = field(default_factory=list)

    @property
    def path(self) -> Path:
        return self.source_file.path

    @property
    def resolved_path(self) -> Path:
        """Resolved path of the file, computed once per source file."""
        return self.source_file.resolved_path

    @property
    def is_suite(self) -> bool:
        return self.collected.is_suite

    @property
    def is_resource(self) -> bool:
        return not self.collected.is_suite and not self.collected.is_init_file

    @property
    def keywords(self) -> list[KeywordDefinition]:
        return self.collected.keywords

    @property
    def usages(self) -> list[KeywordUsage]:
        return self.collected.usages

    @property
    def variables(self) -> list[VariableDefinition]:
        return self.collected.variables

    @property
    def used_variables(self) -> set[str]:
        """Normalized names of variables used anywhere in this file."""
        return self.collected.used_variables

    @property
    def has_dynamic_keyword_calls(self) -> bool:
        """Whether the file calls a keyword using a name built from a variable."""
        return any(usage.name_contains_variable for usage in self.usages)

    def resource_imports(self) -> Iterator[ResolvedImport]:
        """
        Iterate over resource imports of this file.

        Yields:
            Resolved resource imports.

        """
        for imported in self.imports:
            if imported.import_type == ImportType.RESOURCE:
                yield imported

    def library_imports(self) -> Iterator[ResolvedImport]:
        """
        Iterate over library imports of this file.

        Yields:
            Resolved library imports.

        """
        for imported in self.imports:
            if imported.import_type == ImportType.LIBRARY:
                yield imported


class KeywordIndex:
    """Index of keyword definitions in the whole project, allowing lookup by name."""

    def __init__(self) -> None:
        self._by_name: dict[str, list[KeywordDefinition]] = {}
        self._embedded: list[KeywordDefinition] = []

    def add(self, keyword: KeywordDefinition) -> None:
        if keyword.has_embedded_arguments:
            self._embedded.append(keyword)
        else:
            self._by_name.setdefault(keyword.normalized_name, []).append(keyword)

    def find(self, name: str) -> list[KeywordDefinition]:
        """
        Find all definitions that can be called using given name.

        Names prefixed with a resource or library name (``Resource.Keyword``) are looked up using the name without
        the prefix, but only definitions coming from the matching resource file or library are returned.

        Returns:
            List of matching keyword definitions. Empty if no definition matches.

        """
        matches = self._find_by_name(name)
        if matches or "." not in name:
            return matches
        prefix, _, without_prefix = name.rpartition(".")
        return [keyword for keyword in self._find_by_name(without_prefix) if keyword.matches_owner(prefix)]

    def _find_by_name(self, name: str) -> list[KeywordDefinition]:
        """
        Find definitions matching the name exactly, without taking the resource or library prefix into account.

        Returns:
            List of matching keyword definitions. Empty if no definition matches.

        """
        matches = list(self._by_name.get(normalize_robot_name(name), []))
        matches.extend(keyword for keyword in self._embedded if keyword.matches(name))
        return matches

    def __iter__(self) -> Iterator[KeywordDefinition]:
        for definitions in self._by_name.values():
            yield from definitions
        yield from self._embedded


@dataclass
class ProjectContext:
    """
    Context of the whole project, available to project level checkers.

    Attributes:
        root: Root directory of the project.
        files: All parsed source files, keyed by resolved path.
        keywords: Index of all keyword definitions found in the project.
        library_loader: Loader used to import libraries, or None when library analysis is disabled.

    """

    root: Path
    files: dict[Path, ProjectFile] = field(default_factory=dict)
    keywords: KeywordIndex = field(default_factory=KeywordIndex)
    library_loader: LibraryLoader | None = None
    _visible_keywords: dict[Path, KeywordIndex] = field(default_factory=dict, repr=False)
    _library_keywords: dict[Path, list[KeywordDefinition]] = field(default_factory=dict, repr=False)

    def get_file(self, path: Path) -> ProjectFile | None:
        """
        Return project file for given path.

        Returns:
            ProjectFile or None if the path is not part of the project.

        """
        return self.files.get(resolve_path(path))

    def imported_files(self, path: Path) -> list[ProjectFile]:
        """
        Return files visible from given file through resource imports.

        Resource imports are transitive in Robot Framework, so keywords from a resource imported by another resource
        are visible as well. The list starts with the file itself.

        Returns:
            List of project files, starting with the file itself.

        """
        start = self.get_file(path)
        if start is None:
            return []
        visible = [start]
        seen = {start.resolved_path}
        queue = [start]
        while queue:
            current = queue.pop()
            for imported in current.resource_imports():
                if imported.status != ImportStatus.RESOLVED or imported.path is None:
                    continue
                resolved_path = imported.resolved_path
                if resolved_path is None or resolved_path in seen:
                    continue
                imported_file = self.files.get(resolved_path)
                if imported_file is None:
                    continue
                seen.add(resolved_path)
                visible.append(imported_file)
                queue.append(imported_file)
        return visible

    def visible_keywords(self, path: Path) -> KeywordIndex:
        """
        Return index of keywords that can be called from given file.

        Contains keywords defined in the file itself and keywords from all transitively imported resources.
        Private keywords of other files are not included. If library analysis is enabled, keywords from imported
        libraries are included as well.

        Returns:
            KeywordIndex with keywords visible from the file.

        """
        resolved = resolve_path(path)
        cached = self._visible_keywords.get(resolved)
        if cached is not None:
            return cached
        index = KeywordIndex()
        for project_file in self.imported_files(path):
            is_own_file = project_file.resolved_path == resolved
            for keyword in project_file.keywords:
                if keyword.is_private and not is_own_file:
                    continue
                index.add(keyword)
            for keyword in self.library_keywords(project_file):
                index.add(keyword)
        self._visible_keywords[resolved] = index
        return index

    def library_keywords(self, project_file: ProjectFile) -> list[KeywordDefinition]:
        """
        Return keywords from libraries imported by given file.

        Libraries are imported only once and only when this method is called for the first time, so nothing is
        imported if no rule needs the library keywords.

        Returns:
            List of keywords provided by the imported libraries. Empty if library analysis is disabled.

        """
        if self.library_loader is None:
            return []
        resolved = project_file.resolved_path
        cached = self._library_keywords.get(resolved)
        if cached is not None:
            return cached
        keywords: list[KeywordDefinition] = list(self.library_loader.load(BUILTIN_LIBRARY).keywords)
        for imported in project_file.library_imports():
            if imported.status not in (ImportStatus.RESOLVED, ImportStatus.EXTERNAL):
                continue
            spec = self.library_loader.load_import(imported)
            if spec is not None:
                keywords.extend(spec.keywords)
        self._library_keywords[resolved] = keywords
        return keywords

    def resolve_keyword(self, usage: KeywordUsage) -> list[KeywordDefinition]:
        """
        Find definitions matching the keyword usage, using imports of the file the usage comes from.

        Returns:
            List of matching definitions. Empty when the keyword is not defined in the project, for example when it
            comes from a library.

        """
        if usage.name_contains_variable:
            return []
        index = self.visible_keywords(usage.location.source)
        for name in usage.names_to_check():
            matches = index.find(name)
            if matches:
                return matches
        return []

    def iter_files(self) -> Iterator[ProjectFile]:
        """
        Iterate over all files in the project.

        Yields:
            ProjectFile for every parsed source file.

        """
        yield from self.files.values()

    def iter_usages(self) -> Iterator[tuple[ProjectFile, KeywordUsage]]:
        """
        Iterate over all keyword usages in the project.

        Yields:
            Tuples of the file containing the call and the keyword usage.

        """
        for project_file in self.files.values():
            for usage in project_file.usages:
                yield project_file, usage

    def iter_imports(self) -> Iterator[tuple[ProjectFile, ResolvedImport]]:
        """
        Iterate over all imports in the project.

        Yields:
            Tuples of the importing file and the resolved import.

        """
        for project_file in self.files.values():
            for imported in project_file.imports:
                yield project_file, imported


def collection_hash(languages: Languages | None) -> str:
    """
    Describe the configuration that affects parsing and collecting data from a source file.

    Only the language and the Robot Framework version change what is collected. Options such as selected rules or
    command line variables are applied later, on the already collected data.

    Returns:
        Hash used to invalidate the cached data collected from the source files.

    """
    codes = ":".join(sorted(str(getattr(language, "code", language)) for language in languages or []))
    return sha256(f"{codes}|{ROBOT_VERSION}".encode()).hexdigest()


def collect_file(source_file: SourceFile, cache: RobocopCache | None, config_hash: str) -> CollectedFile:
    """
    Collect keywords, usages, variables and imports from a single source file.

    The result is stored in the cache, so that the file does not have to be parsed again in the next run.

    Raises:
        DataError: If the file cannot be parsed.

    Returns:
        CollectedFile with everything found in the file.

    """
    if cache is not None:
        cached = cache.get_project_entry(source_file.path, config_hash)
        if cached is not None:
            collected = collected_file_from_dict(cached, source_file.path)
            if collected is not None:
                return collected
    collected = ProjectFileCollector(source_file.path).collect(source_file.model)
    if cache is not None:
        cache.set_project_entry(source_file.path, config_hash, collected_file_to_dict(collected))
    return collected


def build_project_context(config_manager: ConfigManager, silent: bool = False) -> ProjectContext:
    """
    Parse all source files in the project and build the shared context.

    Files that cannot be parsed are skipped, so a single broken file does not prevent project level checks from
    running on the rest of the project.

    Returns:
        ProjectContext with parsed files, keyword index and resolved imports.

    """
    context = ProjectContext(root=config_manager.root)
    config = config_manager.default_config
    search_paths = build_search_paths(config.python_path, config_manager.root)
    cache = config_manager.cache if config.cache.enabled else None
    if config.analyze_libraries:
        context.library_loader = build_library_loader(
            search_paths=search_paths,
            timeout=config.load_library_timeout,
            ignored_libraries=config.ignored_libraries,
            cache=cache,
            project_root=config_manager.root,
            workers=config.library_workers,
        )
    global_scope = VariableScope()
    global_scope.add_variable_files(config.variable_files, search_paths)
    global_scope.add_command_line(config.variables)
    config_hash = collection_hash(config.languages)

    for source_file in config_manager.project_paths:
        try:
            collected = collect_file(source_file, cache, config_hash)
        except DataError as error:
            if not silent:
                print(f"Failed to parse {source_file.path} with an error: {error}. Skipping file")
            continue
        context.files[source_file.resolved_path] = ProjectFile(source_file=source_file, collected=collected)

    for project_file in context.files.values():
        scope = global_scope.copy_for(project_file.path)
        scope.add_own(project_file.variables)
        resolver = ImportResolver(scope, search_paths)
        base_dir = project_file.path.parent
        project_file.imports = [
            resolver.resolve(raw.import_type, raw.name, raw.location, base_dir, raw.args, raw.alias)
            for raw in project_file.collected.imports
        ]
        for keyword in project_file.keywords:
            context.keywords.add(keyword)

    if context.library_loader is not None:
        context.library_loader.schedule_preload(_project_library_requests(context))

    return context


def _project_library_requests(context: ProjectContext) -> Iterator[LibraryRequest]:
    """
    Collect every library imported in the project.

    Yields:
        LibraryRequest for the BuiltIn library and for every resolved library import.

    """
    yield BUILTIN_LIBRARY
    for project_file in context.files.values():
        for imported in project_file.library_imports():
            if imported.status not in (ImportStatus.RESOLVED, ImportStatus.EXTERNAL) or not imported.args_resolved:
                continue
            yield LibraryRequest(
                name=imported.resolved_name,
                args=imported.args,
                source=imported.path,
                alias=imported.alias,
            )
