"""Checkers for the rules defined in ``robocop.linter.rules.usage``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import ProjectChecker, usage
from robocop.linter.utils.misc import normalize_robot_name
from robocop.project.definitions import usage_name_pattern
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    import re
    from pathlib import Path

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext, ProjectFile
    from robocop.project.definitions import KeywordDefinition
    from robocop.source_file import VirtualSourceFile


class UsedKeywordNames:
    """Names used to call keywords, collected from a set of files."""

    def __init__(self) -> None:
        self.normalized: set[str] = set()
        self.names: list[str] = []
        self.dynamic_patterns: list[re.Pattern[str]] = []

    def add(self, name: str, name_contains_variable: bool) -> None:
        """Record a name used to call a keyword."""
        if name_contains_variable:
            pattern = usage_name_pattern(name)
            if pattern is not None:
                self.dynamic_patterns.append(pattern)
            return
        self.names.append(name)
        self.normalized.add(normalize_robot_name(name))
        if "." in name:
            _, _, without_prefix = name.rpartition(".")
            self.normalized.add(normalize_robot_name(without_prefix))
            self.names.append(without_prefix)

    def uses(self, keyword: KeywordDefinition) -> bool:
        """
        Check if the keyword is called by any of the collected names.

        Returns:
            True if any collected name refers to this keyword.

        """
        if keyword.has_embedded_arguments:
            if any(keyword.matches(name) for name in self.names):
                return True
        elif keyword.normalized_name in self.normalized:
            return True
        return any(pattern.fullmatch(keyword.normalized_name) for pattern in self.dynamic_patterns)


class UnusedKeywords(ProjectChecker):
    """Reports keywords that are never called in the project."""

    unused_keyword: usage.UnusedKeywordRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext | None = None,
    ) -> list[Diagnostic]:
        self.issues = []
        if context is None:
            return self.issues
        project_usages, file_usages = self._collect_usages(context)
        for project_file in context.iter_files():
            private_usages = file_usages.get(project_file.path.resolve())
            for keyword in project_file.keywords:
                usages = private_usages if keyword.is_private else project_usages
                if usages is not None and usages.uses(keyword):
                    continue
                self._report_keyword(project_file, keyword, project_source_file)
        return self.issues

    def _report_keyword(
        self,
        project_file: ProjectFile,
        keyword: KeywordDefinition,
        project_source_file: SourceFile | VirtualSourceFile,
    ) -> None:
        self.report(
            self.unused_keyword,
            source=SourceFile(path=project_file.path, config=project_source_file.config),
            keyword_name=keyword.name,
            lineno=keyword.location.lineno,
            col=keyword.location.col,
            end_lineno=keyword.location.end_lineno,
            end_col=keyword.location.end_col,
        )

    @staticmethod
    def _collect_usages(context: ProjectContext) -> tuple[UsedKeywordNames, dict[Path, UsedKeywordNames]]:
        """
        Collect names used to call keywords, for the whole project and for every file separately.

        Returns:
            Tuple of names used anywhere in the project and names used in each file.

        """
        project_usages = UsedKeywordNames()
        file_usages: dict[Path, UsedKeywordNames] = {}
        for project_file, usage in context.iter_usages():
            per_file = file_usages.setdefault(project_file.path.resolve(), UsedKeywordNames())
            for name in usage.names_to_check():
                project_usages.add(name, usage.name_contains_variable)
                per_file.add(name, usage.name_contains_variable)
        return project_usages, file_usages
