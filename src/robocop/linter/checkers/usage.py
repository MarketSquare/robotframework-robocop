"""Checkers for the rules defined in ``robocop.linter.rules.usage``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.libraries import STDLIBS

from robocop.files import path_relative_to_cwd
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
    from robocop.project.definitions import KeywordDefinition, KeywordUsage
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


class AmbiguousKeywordNames(ProjectChecker):
    """Reports keyword calls matching keywords defined in more than one place."""

    ambiguous_keyword_name: usage.AmbiguousKeywordNameRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        for project_file, keyword_usage in context.iter_usages():
            candidates = self._ambiguous_definitions(context, keyword_usage)
            if not candidates:
                continue
            self.report(
                self.ambiguous_keyword_name,
                source=SourceFile(path=project_file.path, config=project_source_file.config),
                keyword_name=keyword_usage.name,
                sources=_describe_sources(candidates),
                lineno=keyword_usage.location.lineno,
                col=keyword_usage.location.col,
                end_lineno=keyword_usage.location.end_lineno,
                end_col=keyword_usage.location.end_col,
            )
        return self.issues

    @staticmethod
    def _ambiguous_definitions(context: ProjectContext, keyword_usage: KeywordUsage) -> list[KeywordDefinition]:
        """
        Find definitions the call can refer to, if there is more than one to choose from.

        Returns:
            List of definitions with the same priority, or an empty list if the call is not ambiguous.

        """
        if keyword_usage.name_contains_variable:
            return []
        index = context.visible_keywords(keyword_usage.location.source)
        for name in keyword_usage.names_to_check():
            matches = index.find(name)
            if not matches:
                continue
            # names matched only after removing the resource or library prefix are explicit already
            direct = [definition for definition in matches if definition.matches(name)]
            if not direct:
                return []
            return _same_priority(_unique(direct), keyword_usage.location.source)
        return []


def _unique(definitions: list[KeywordDefinition]) -> list[KeywordDefinition]:
    """
    Remove definitions pointing to the same keyword.

    The same library can be imported by several files, each import providing its own copy of the keywords.

    Returns:
        List of definitions without duplicates, in the original order.

    """
    unique: list[KeywordDefinition] = []
    seen: set[tuple[str, int, str]] = set()
    for definition in definitions:
        key = (str(definition.location.source), definition.location.lineno, definition.normalized_name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(definition)
    return unique


def _same_priority(definitions: list[KeywordDefinition], source: Path) -> list[KeywordDefinition]:
    """
    Return definitions Robot Framework cannot choose between.

    Returns:
        List of definitions with the same priority, or an empty list if one of them wins.

    """
    if len(definitions) < 2:
        return []
    if any(definition.has_embedded_arguments for definition in definitions):
        return []  # Robot Framework prefers the most specific match
    own_file = [definition for definition in definitions if definition.location.source == source]
    if own_file:
        return []  # keyword from the same file wins, duplicates in a single file are reported by another rule
    user_keywords = [definition for definition in definitions if not definition.is_from_library]
    if user_keywords:
        return user_keywords if len(user_keywords) > 1 else []
    custom_libraries = [definition for definition in definitions if definition.library_name not in STDLIBS]
    if custom_libraries:
        return custom_libraries if len(custom_libraries) > 1 else []
    return definitions


def _describe_sources(definitions: list[KeywordDefinition]) -> str:
    """
    Describe where the matching keywords are defined.

    Returns:
        Comma separated list of libraries and files defining the keyword.

    """
    sources = []
    for definition in definitions:
        source = definition.library_name or str(path_relative_to_cwd(definition.location.source))
        if source not in sources:
            sources.append(source)
    return ", ".join(sources)


class UnusedKeywords(ProjectChecker):
    """Reports keywords that are never called in the project."""

    unused_keyword: usage.UnusedKeywordRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
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
        for project_file, keyword_usage in context.iter_usages():
            per_file = file_usages.setdefault(project_file.path.resolve(), UsedKeywordNames())
            for name in keyword_usage.names_to_check():
                project_usages.add(name, keyword_usage.name_contains_variable)
                per_file.add(name, keyword_usage.name_contains_variable)
        return project_usages, file_usages
