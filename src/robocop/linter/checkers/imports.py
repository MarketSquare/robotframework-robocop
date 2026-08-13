"""Checkers for the rules defined in ``robocop.linter.rules.imports``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker, imports
from robocop.project.definitions import ImportStatus, ImportType
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext
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
