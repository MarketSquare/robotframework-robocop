"""Checkers for the rules defined in ``robocop.linter.rules.imports``."""

from __future__ import annotations

import os
import re
from collections import deque
from typing import TYPE_CHECKING

from robocop.files import path_relative_to_cwd, resolve_path
from robocop.linter.rules import ProjectChecker, imports
from robocop.project.context import KeywordIndex
from robocop.project.definitions import ImportStatus, ImportType
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from pathlib import Path

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.rules import Rule
    from robocop.project.context import ProjectContext, ProjectFile
    from robocop.project.definitions import ResolvedImport
    from robocop.source_file import VirtualSourceFile

NOT_IMPORTED_LIBRARIES = frozenset({"Remote"})
"""Libraries that are never imported, since importing them requires a running service."""

IMPORT_ERROR_PREFIX = re.compile(r"^(?:\w+: )?Importing (?:test )?library '[^']*' failed: ")


def _import_error(error: str | None) -> str:
    """
    Make the error returned by the library import shorter.

    Robot Framework prefixes the error with the name of the library, which is already a part of the reported
    message.

    Returns:
        Error without the redundant prefix.

    """
    if not error:
        return "Unknown error"
    return IMPORT_ERROR_PREFIX.sub("", error)


class ProjectImportsChecker(ProjectChecker):
    """Checker for imports that can only be validated with the whole project context."""

    unresolved_resource_import: imports.UnresolvedResourceImportRule
    unresolved_library_import: imports.UnresolvedLibraryImportRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        for project_file, imported in context.iter_imports():
            if imported.import_type == ImportType.RESOURCE:
                if imported.status == ImportStatus.NOT_FOUND:
                    self._report_import(self.unresolved_resource_import, project_file, imported, project_source_file)
            elif imported.import_type == ImportType.LIBRARY:
                self._check_library(project_file, imported, project_source_file, context)
        return self.issues

    def _check_library(
        self,
        project_file: ProjectFile,
        imported: ResolvedImport,
        project_source_file: SourceFile | VirtualSourceFile,
        context: ProjectContext,
    ) -> None:
        """Report library import that Robot Framework would not be able to import."""
        if imported.status == ImportStatus.UNRESOLVABLE or not imported.args_resolved:
            return
        if imported.resolved_name in NOT_IMPORTED_LIBRARIES:
            return
        loader = context.library_loader
        if loader is not None and loader.is_ignored(imported.resolved_name):
            return
        if imported.status == ImportStatus.NOT_FOUND:
            error = "File does not exist"
        else:
            if loader is None:
                return
            spec = loader.load_import(imported)
            if spec is None or spec.loaded:
                return
            error = _import_error(spec.error)
        self._report_import(self.unresolved_library_import, project_file, imported, project_source_file, error=error)

    def _report_import(
        self,
        rule: Rule,
        project_file: ProjectFile,
        imported: ResolvedImport,
        project_source_file: SourceFile | VirtualSourceFile,
        error: str = "",
    ) -> None:
        """Report the import using the location of the import statement."""
        self.report(
            rule,
            source=SourceFile(path=project_file.path, config=project_source_file.config),
            import_name=imported.resolved_name,
            error=error,
            lineno=imported.location.lineno,
            col=imported.location.col,
            end_lineno=imported.location.end_lineno,
            end_col=imported.location.end_col,
        )


class UnusedImportsChecker(ProjectChecker):
    """Checker reporting imports that are not used by the importing file."""

    unused_resource_import: imports.UnusedResourceImportRule
    unused_library_import: imports.UnusedLibraryImportRule

    def __init__(self) -> None:
        super().__init__()
        self._importers: dict[Path, list[ProjectFile]] | None = None

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        self._importers = None
        for project_file in context.iter_files():
            self._check_file(project_file, project_source_file, context)
        return self.issues

    def _check_file(
        self,
        project_file: ProjectFile,
        project_source_file: SourceFile | VirtualSourceFile,
        context: ProjectContext,
    ) -> None:
        consumers = self._consumers_of(project_file, context)
        if any(consumer.has_dynamic_keyword_calls for consumer in consumers):
            return
        used_keywords, used_variables = _collect_usage(consumers)
        own_path = project_file.resolved_path
        for imported in project_file.resource_imports():
            imported_path = imported.resolved_path
            if imported.status != ImportStatus.RESOLVED or imported_path is None:
                continue
            resource = context.files.get(imported_path)
            if resource is None or resource.resolved_path == own_path:
                continue
            if _is_used(resource, context, used_keywords, used_variables):
                continue
            self.report(
                self.unused_resource_import,
                source=SourceFile(path=project_file.path, config=project_source_file.config),
                import_name=imported.name,
                lineno=imported.location.lineno,
                col=imported.location.col,
                end_lineno=imported.location.end_lineno,
                end_col=imported.location.end_col,
            )
        self._check_libraries(project_file, project_source_file, context, used_keywords)

    def _check_libraries(
        self,
        project_file: ProjectFile,
        project_source_file: SourceFile | VirtualSourceFile,
        context: ProjectContext,
        used_keywords: set[str],
    ) -> None:
        """Report library imports whose keywords are not used."""
        if context.library_loader is None:
            return
        for imported in project_file.library_imports():
            if imported.status not in (ImportStatus.RESOLVED, ImportStatus.EXTERNAL):
                continue
            spec = context.library_loader.load_import(imported)
            if spec is None or not spec.loaded or not spec.keywords:
                continue
            index = KeywordIndex()
            for keyword in spec.keywords:
                index.add(keyword)
            if any(index.find(name) for name in used_keywords):
                continue
            self.report(
                self.unused_library_import,
                source=SourceFile(path=project_file.path, config=project_source_file.config),
                import_name=imported.alias or imported.name,
                lineno=imported.location.lineno,
                col=imported.location.col,
                end_lineno=imported.location.end_lineno,
                end_col=imported.location.end_col,
            )

    def _consumers_of(self, project_file: ProjectFile, context: ProjectContext) -> list[ProjectFile]:
        """
        Return files whose keyword calls may rely on imports of given file.

        Resource imports are transitive, so a resource may be imported only to make its own imports available to files
        importing it. Suite initialization files share imports with all files in the directory.

        Returns:
            List of project files that see the imports of given file, including the file itself.

        """
        if project_file.collected.is_init_file:
            # comparing string prefixes is much faster than Path.is_relative_to, which walks all parents
            directory = f"{resolve_path(project_file.path.parent)}{os.sep}"
            return [other for other in context.iter_files() if str(other.resolved_path).startswith(directory)]
        if project_file.is_suite:
            return [project_file]
        if self._importers is None:
            self._importers = _build_importers(context)
        return self._importers.get(project_file.resolved_path, [project_file])


class CircularImports(ProjectChecker):
    """Checker reporting resource imports that take part in a circular import."""

    circular_import: imports.CircularImportRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        for project_file in context.iter_files():
            own_path = project_file.resolved_path
            for imported in project_file.resource_imports():
                if imported.status != ImportStatus.RESOLVED or imported.path is None:
                    continue
                imported_path = imported.resolved_path
                if imported_path not in context.files:
                    continue
                cycle = _path_back_to(context, imported_path, own_path)
                if cycle is None:
                    continue
                self.report(
                    self.circular_import,
                    source=SourceFile(path=project_file.path, config=project_source_file.config),
                    cycle=" -> ".join(str(path_relative_to_cwd(path)) for path in [own_path, *cycle]),
                    lineno=imported.location.lineno,
                    col=imported.location.col,
                    end_lineno=imported.location.end_lineno,
                    end_col=imported.location.end_col,
                )
        return self.issues


def _path_back_to(context: ProjectContext, start: Path, target: Path) -> list[Path] | None:
    """
    Find the shortest chain of resource imports leading from the imported file back to the importing one.

    Returns:
        List of paths from the imported file to the target, or None if the target is not imported back.

    """
    queue: deque[tuple[Path, list[Path]]] = deque([(start, [start])])
    seen = {start}
    while queue:
        current, chain = queue.popleft()
        if current == target:
            return chain
        project_file = context.files.get(current)
        if project_file is None:
            continue
        for imported in project_file.resource_imports():
            if imported.status != ImportStatus.RESOLVED or imported.path is None:
                continue
            next_path = imported.resolved_path
            if next_path == target:
                return [*chain, next_path]
            if next_path is None or next_path in seen or next_path not in context.files:
                continue
            seen.add(next_path)
            queue.append((next_path, [*chain, next_path]))
    return None


def _build_importers(context: ProjectContext) -> dict[Path, list[ProjectFile]]:
    """
    Map every file to the files that see it through transitive resource imports.

    Returns:
        Dictionary of resolved path to the list of files importing it, each including the file itself.

    """
    importers: dict[Path, list[ProjectFile]] = {}
    for project_file in context.iter_files():
        for visible in context.imported_files(project_file.path):
            importers.setdefault(visible.resolved_path, []).append(project_file)
    return importers


def _collect_usage(files: list[ProjectFile]) -> tuple[set[str], set[str]]:
    """
    Collect keyword names and variable names used in given files.

    Returns:
        Tuple of keyword usage names to check and normalized variable names.

    """
    used_keywords: set[str] = set()
    used_variables: set[str] = set()
    for project_file in files:
        for usage in project_file.usages:
            used_keywords.update(usage.names_to_check())
        used_variables.update(project_file.used_variables)
    return used_keywords, used_variables


def _is_used(
    resource: ProjectFile,
    context: ProjectContext,
    used_keywords: set[str],
    used_variables: set[str],
) -> bool:
    """
    Check whether anything provided by the resource is used.

    Resources without keywords and variables are never reported, since they may be imported only for the imports
    they make themselves. Keywords coming from libraries are ignored, since the importing file can use them without
    importing the resource.

    Returns:
        True if the resource provides nothing or if any of its keywords or variables is used.

    """
    index = KeywordIndex()
    for keyword in context.visible_keywords(resource.path):
        if not keyword.is_from_library:
            index.add(keyword)
    variables = {
        variable.normalized_name for file in context.imported_files(resource.path) for variable in file.variables
    }
    if not variables and not any(True for _ in index):
        return True
    if used_variables & variables:
        return True
    return any(index.find(name) for name in used_keywords)
