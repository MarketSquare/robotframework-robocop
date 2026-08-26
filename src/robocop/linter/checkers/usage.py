"""Checkers for the rules defined in ``robocop.linter.rules.usage``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.libraries import STDLIBS

from robocop.files import path_relative_to_cwd
from robocop.linter.rules import ProjectChecker, usage
from robocop.linter.utils.misc import normalize_robot_name
from robocop.project.context import BUILTIN_LIBRARY
from robocop.project.definitions import ImportStatus, ImportType, usage_name_pattern
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    import re
    from pathlib import Path

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.project.context import ProjectContext, ProjectFile
    from robocop.project.definitions import KeywordDefinition, KeywordUsage, ResolvedImport
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


DYNAMIC_IMPORT_KEYWORDS = frozenset({"importlibrary", "importresource"})
"""Keywords that add keywords to the file at runtime, making static analysis incomplete."""

RESERVED_KEYWORD_NAMES = frozenset({"none"})
"""Values used in place of a keyword name that do not refer to any keyword."""


class KeywordUsageChecker(ProjectChecker):
    """Checker for rules validated against every keyword call in the project."""

    keyword_not_found: usage.KeywordNotFoundRule
    ambiguous_keyword_name: usage.AmbiguousKeywordNameRule
    missing_keyword_prefix: usage.MissingKeywordPrefixRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        # without libraries almost every call would be reported as not found
        check_not_found = self.keyword_not_found.enabled and context.library_loader is not None
        check_ambiguous = self.ambiguous_keyword_name.enabled
        check_prefix = self.missing_keyword_prefix.enabled
        can_check: dict[Path, bool] = {}
        for project_file, keyword_usage in context.iter_usages():
            if check_not_found:
                self._check_not_found(context, project_file, keyword_usage, project_source_file, can_check)
            if check_ambiguous:
                self._check_ambiguous(context, project_file, keyword_usage, project_source_file)
            if check_prefix:
                self._check_prefix(context, project_file, keyword_usage, project_source_file)
        return self.issues

    def _check_not_found(
        self,
        context: ProjectContext,
        project_file: ProjectFile,
        keyword_usage: KeywordUsage,
        project_source_file: SourceFile | VirtualSourceFile,
        can_check: dict[Path, bool],
    ) -> None:
        if self._is_known(context, keyword_usage) or not self._can_be_checked(context, project_file, can_check):
            return
        self.report(
            self.keyword_not_found,
            source=SourceFile(path=project_file.path, config=project_source_file.config),
            keyword_name=keyword_usage.name,
            lineno=keyword_usage.location.lineno,
            col=keyword_usage.location.col,
            end_lineno=keyword_usage.location.end_lineno,
            end_col=keyword_usage.location.end_col,
        )

    def _check_ambiguous(
        self,
        context: ProjectContext,
        project_file: ProjectFile,
        keyword_usage: KeywordUsage,
        project_source_file: SourceFile | VirtualSourceFile,
    ) -> None:
        candidates = self._ambiguous_definitions(context, keyword_usage)
        if not candidates:
            return
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

    def _check_prefix(
        self,
        context: ProjectContext,
        project_file: ProjectFile,
        keyword_usage: KeywordUsage,
        project_source_file: SourceFile | VirtualSourceFile,
    ) -> None:
        prefix = self._find_prefix(context, keyword_usage)
        if prefix is None:
            return
        self.report(
            self.missing_keyword_prefix,
            source=SourceFile(path=project_file.path, config=project_source_file.config),
            keyword_name=keyword_usage.name,
            prefix=prefix,
            prefix_offset=_bdd_prefix_offset(keyword_usage),
            lineno=keyword_usage.location.lineno,
            col=keyword_usage.location.col,
            end_lineno=keyword_usage.location.end_lineno,
            end_col=keyword_usage.location.end_col,
        )

    def _find_prefix(self, context: ProjectContext, keyword_usage: KeywordUsage) -> str | None:
        """
        Find the prefix the call should use.

        Returns:
            Name of the resource file or library, or None if the call should not be reported.

        """
        if keyword_usage.name_contains_variable or keyword_usage.is_template:
            return None
        name = keyword_usage.names_to_check()[-1]
        if "." in name:
            return None  # already prefixed, or the name contains a dot and cannot be prefixed safely
        definitions = context.resolve_keyword(keyword_usage)
        if len(definitions) != 1:
            return None  # not defined in the project, or ambiguous
        definition = definitions[0]
        if definition.location.source == keyword_usage.location.source:
            return None  # keyword defined in the file with the call, there is nothing to prefix it with
        # keywords from the libraries imported with the ``AS`` syntax already use the alias as the library name
        prefix = definition.library_name or definition.location.source.stem
        if normalize_robot_name(prefix) in self.missing_keyword_prefix.ignored_sources:
            return None
        return prefix

    @staticmethod
    def _is_known(context: ProjectContext, keyword_usage: KeywordUsage) -> bool:
        """
        Check if the call can be matched to a keyword definition.

        Returns:
            True if the keyword is defined or cannot be resolved statically.

        """
        if keyword_usage.name_contains_variable or keyword_usage.normalized_name in RESERVED_KEYWORD_NAMES:
            return True
        return bool(context.resolve_keyword(keyword_usage))

    @staticmethod
    def _can_be_checked(context: ProjectContext, project_file: ProjectFile, cache: dict[Path, bool]) -> bool:
        """
        Check if all keywords available in the file are known.

        Returns:
            True if every import of the file and of its resources was resolved and loaded.

        """
        resolved = project_file.resolved_path
        cached = cache.get(resolved)
        if cached is not None:
            return cached
        can_check = KeywordUsageChecker._all_imports_known(context, project_file)
        cache[resolved] = can_check
        return can_check

    @staticmethod
    def _all_imports_known(context: ProjectContext, project_file: ProjectFile) -> bool:
        """
        Check imports of the file and of all resources it imports.

        Returns:
            True if nothing is missing from the keywords visible in the file.

        """
        loader = context.library_loader
        if loader is None or not loader.load(BUILTIN_LIBRARY).loaded:
            return False
        for visible_file in context.imported_files(project_file.path):
            if any(keyword_usage.normalized_name in DYNAMIC_IMPORT_KEYWORDS for keyword_usage in visible_file.usages):
                return False
            if not all(KeywordUsageChecker._import_known(context, imported) for imported in visible_file.imports):
                return False
        return True

    @staticmethod
    def _import_known(context: ProjectContext, imported: ResolvedImport) -> bool:
        """
        Check if the import provides keywords that are known to Robocop.

        Returns:
            True if the import cannot hide any keyword.

        """
        if imported.import_type == ImportType.VARIABLES:
            return True
        if imported.status not in (ImportStatus.RESOLVED, ImportStatus.EXTERNAL):
            return False
        if imported.import_type == ImportType.RESOURCE:
            return imported.resolved_path is not None and imported.resolved_path in context.files
        if not imported.args_resolved or context.library_loader is None:
            return False
        spec = context.library_loader.load_import(imported)
        return spec is not None and spec.loaded

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


def _bdd_prefix_offset(keyword_usage: KeywordUsage) -> int:
    """
    Find where the keyword name starts, ignoring the BDD prefix.

    The prefix is added after the BDD word, so that ``Given Login`` becomes ``Given login.Login``.

    Returns:
        Number of characters between the start of the call and the start of the keyword name.

    """
    if keyword_usage.bdd_prefix is None:
        return 0
    return len(keyword_usage.name) - len(keyword_usage.names_to_check()[-1])


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
            private_usages = file_usages.get(project_file.resolved_path)
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
        for project_file in context.iter_files():
            per_file = file_usages.setdefault(project_file.resolved_path, UsedKeywordNames())
            for keyword_usage in project_file.usages:
                for name in keyword_usage.names_to_check():
                    project_usages.add(name, keyword_usage.name_contains_variable)
                    per_file.add(name, keyword_usage.name_contains_variable)
        return project_usages, file_usages
