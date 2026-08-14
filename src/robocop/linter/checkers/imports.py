"""Checkers for the rules defined in ``robocop.linter.rules.imports``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker, imports
from robocop.project.context import KeywordIndex
from robocop.project.definitions import ImportStatus, ImportType
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from pathlib import Path

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext, ProjectFile
    from robocop.source_file import VirtualSourceFile


class ProjectImportsChecker(ProjectChecker):
    """Checker for imports that can only be validated with the whole project context."""

    unresolved_resource_import: imports.UnresolvedResourceImportRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext | None = None,
    ) -> list[Diagnostic]:
        self.issues = []
        if context is None:
            return self.issues
        for project_file, imported in context.iter_imports():
            if imported.import_type != ImportType.RESOURCE or imported.status != ImportStatus.NOT_FOUND:
                continue
            self.report(
                self.unresolved_resource_import,
                source=SourceFile(path=project_file.path, config=project_source_file.config),
                import_name=imported.resolved_name,
                lineno=imported.location.lineno,
                col=imported.location.col,
                end_lineno=imported.location.end_lineno,
                end_col=imported.location.end_col,
            )
        return self.issues


class UnusedImportsChecker(ProjectChecker):
    """Checker reporting imports that are not used by the importing file."""

    unused_resource_import: imports.UnusedResourceImportRule

    def __init__(self) -> None:
        super().__init__()
        self._importers: dict[Path, list[ProjectFile]] | None = None

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext | None = None,
    ) -> list[Diagnostic]:
        self.issues = []
        self._importers = None
        if context is None:
            return self.issues
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
        own_path = project_file.path.resolve()
        for imported in project_file.resource_imports():
            if imported.status != ImportStatus.RESOLVED or imported.path is None:
                continue
            resource = context.files.get(imported.path.resolve())
            if resource is None or resource.path.resolve() == own_path:
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

    def _consumers_of(self, project_file: ProjectFile, context: ProjectContext) -> list[ProjectFile]:
        """
        Return files whose keyword calls may rely on imports of given file.

        Resource imports are transitive, so a resource may be imported only to make its own imports available to files
        importing it. Suite initialization files share imports with all files in the directory.

        Returns:
            List of project files that see the imports of given file, including the file itself.

        """
        if project_file.collected.is_init_file:
            directory = project_file.path.parent.resolve()
            return [other for other in context.iter_files() if directory in other.path.resolve().parents]
        if project_file.is_suite:
            return [project_file]
        if self._importers is None:
            self._importers = _build_importers(context)
        return self._importers.get(project_file.path.resolve(), [project_file])


def _build_importers(context: ProjectContext) -> dict[Path, list[ProjectFile]]:
    """
    Map every file to the files that see it through transitive resource imports.

    Returns:
        Dictionary of resolved path to the list of files importing it, each including the file itself.

    """
    importers: dict[Path, list[ProjectFile]] = {}
    for project_file in context.iter_files():
        for visible in context.imported_files(project_file.path):
            importers.setdefault(visible.path.resolve(), []).append(project_file)
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
