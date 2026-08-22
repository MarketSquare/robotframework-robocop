"""Checkers for the rules defined in ``robocop.linter.rules.duplications``."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, NamedTuple

from robot.api import Token

from robocop.linter.rules import ProjectChecker, Rule, VisitorChecker, duplications, variables
from robocop.linter.utils.misc import (
    normalize_robot_name,
    normalize_robot_var_name,
    strip_equals_from_assignment,
)
from robocop.source_file import SourceFile
from robocop.version_handling import TYPE_SUPPORTED

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing import File
    from robot.parsing.model.blocks import Keyword, TestCase, VariableSection
    from robot.parsing.model.statements import (
        Error,
        KeywordCall,
        LibraryImport,
        Metadata,
        ResourceImport,
        Variable,
        VariablesImport,
    )

    from robocop.config.manager import ConfigManager
    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.rules.duplications import NodeT
    from robocop.project.context import ProjectContext, ProjectFile
    from robocop.project.definitions import Location, VariableDefinition
    from robocop.source_file import VirtualSourceFile


class DuplicationsChecker(VisitorChecker):
    """Checker for duplicated names."""

    duplicated_test_case: duplications.DuplicatedTestCaseRule
    duplicated_keyword: duplications.DuplicatedKeywordRule
    duplicated_variable: duplications.DuplicatedVariableRule
    duplicated_resource: duplications.DuplicatedResourceRule
    duplicated_library: duplications.DuplicatedLibraryRule
    duplicated_metadata: duplications.DuplicatedMetadataRule
    duplicated_variables_import: duplications.DuplicatedVariablesImportRule
    duplicated_assigned_var_name: variables.DuplicatedAssignedVarNameRule
    duplicated_setting: duplications.DuplicatedSettingRule

    def __init__(self) -> None:
        self.test_cases: defaultdict[str, list[TestCase]] = defaultdict(list)
        self.keywords: defaultdict[str, list[Keyword]] = defaultdict(list)
        self.variables: defaultdict[str, list[Variable]] = defaultdict(list)
        self.resources: defaultdict[str, list[ResourceImport]] = defaultdict(list)
        self.libraries: defaultdict[str, list[LibraryImport]] = defaultdict(list)
        self.metadata: defaultdict[str, list[Metadata]] = defaultdict(list)
        self.variable_imports: defaultdict[str, list[VariablesImport]] = defaultdict(list)
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.test_cases = defaultdict(list)
        self.keywords = defaultdict(list)
        self.variables = defaultdict(list)
        self.resources = defaultdict(list)
        self.libraries = defaultdict(list)
        # only the suite metadata, test case metadata is scoped to its test case in ``visit_TestCase``
        self.metadata = defaultdict(list)
        self.variable_imports = defaultdict(list)
        super().visit_File(node)
        self.check_duplicates(self.test_cases, self.duplicated_test_case)
        self.check_duplicates(self.keywords, self.duplicated_keyword)
        self.check_duplicates(self.variables, self.duplicated_variable)
        self.check_duplicates(self.resources, self.duplicated_resource, underline_whole_line=True)
        self.check_duplicates(self.metadata, self.duplicated_metadata, underline_whole_line=True)
        self.check_duplicates(self.variable_imports, self.duplicated_variables_import, underline_whole_line=True)
        self.check_library_duplicates(self.libraries, self.duplicated_library)

    def check_duplicates(
        self, container: defaultdict[str, list[NodeT]], rule: Rule, underline_whole_line: bool = False
    ) -> None:
        for nodes in container.values():
            for duplicate in nodes[1:]:
                # the statement can be indented (test case ``[Metadata]``), point at the setting name itself
                data_tokens = getattr(duplicate, "data_tokens", None)
                col = (data_tokens[0].col_offset if data_tokens else duplicate.col_offset) + 1
                if underline_whole_line:
                    end_col = duplicate.end_col_offset
                else:
                    end_col = duplicate.col_offset + len(duplicate.name) + 1
                self.report(
                    rule,
                    name=duplicate.name,
                    first_occurrence_line=nodes[0].lineno,
                    node=duplicate,
                    col=col,
                    end_col=end_col,
                )

    def check_library_duplicates(self, container: defaultdict[str, list[LibraryImport]], rule: Rule) -> None:
        for nodes in container.values():
            for duplicate in nodes[1:]:
                lib_token = duplicate.get_token(Token.NAME)
                self.report(
                    rule,
                    name=duplicate.name,
                    first_occurrence_line=nodes[0].lineno,
                    node=duplicate,
                    col=lib_token.col_offset + 1,
                    end_col=lib_token.end_col_offset + 1,
                )

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        testcase_name = normalize_robot_name(node.name)
        self.test_cases[testcase_name].append(node)
        # Robot Framework 7.5 allows ``[Metadata]`` in test cases. Such metadata is scoped to the test case,
        # so it can repeat the suite metadata or the metadata of a different test without being a duplicate.
        outer_metadata, self.metadata = self.metadata, defaultdict(list)
        self.generic_visit(node)
        self.check_duplicates(self.metadata, self.duplicated_metadata, underline_whole_line=True)
        self.metadata = outer_metadata

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        keyword_name = normalize_robot_name(node.name)
        self.keywords[keyword_name].append(node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        assign = node.get_tokens(Token.ASSIGN)
        seen = set()
        for var in assign:
            var_name = strip_equals_from_assignment(var.value)
            name = normalize_robot_var_name(var_name, strip_type=TYPE_SUPPORTED)
            if not name:  # i.e. "${_}" -> ""
                return
            if name in seen:
                self.report(
                    self.duplicated_assigned_var_name,
                    variable_name=var_name,
                    node=node,
                    lineno=var.lineno,
                    col=var.col_offset + 1,
                    end_col=var.col_offset + len(var.value) + 1,
                )
            else:
                seen.add(name)

    def visit_VariableSection(self, node: VariableSection) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_Variable(self, node: Variable) -> None:  # noqa: N802
        if not node.name or node.errors:
            return
        var_name = normalize_robot_name(self.replace_chars(node.name, "${}@&"))
        self.variables[var_name].append(node)

    @staticmethod
    def replace_chars(name: str, chars: str) -> str:
        return "".join(c for c in name if c not in chars)

    def visit_ResourceImport(self, node: ResourceImport) -> None:  # noqa: N802
        if node.name:
            self.resources[node.name].append(node)

    def visit_LibraryImport(self, node: LibraryImport) -> None:  # noqa: N802
        if not node.name:
            return
        lib_name = node.alias if node.alias else node.name
        name_with_args = lib_name + "".join(token.value for token in node.get_tokens(Token.ARGUMENT))
        self.libraries[name_with_args].append(node)

    def visit_Metadata(self, node: Metadata) -> None:  # noqa: N802
        if node.name is not None:
            self.metadata[node.name + node.value].append(node)

    def visit_VariablesImport(self, node: VariablesImport) -> None:  # noqa: N802
        if not node.name:
            return
        # only YAML files can't have arguments - covered in E0404 variables-import-with-args
        if node.name.endswith((".yaml", ".yml")) and node.get_token(Token.ARGUMENT):
            return
        name_with_args = node.name + "".join(token.value for token in node.data_tokens[2:])
        self.variable_imports[name_with_args].append(node)

    def visit_Error(self, node: Error) -> None:  # noqa: N802
        for error in node.errors:
            if "is allowed only once" in error:
                self.report(
                    self.duplicated_setting,
                    error_msg=error,
                    node=node,
                    col=node.data_tokens[0].col_offset + 1,
                    end_col=node.data_tokens[0].end_col_offset + 1,
                )


class VariableOccurrence(NamedTuple):
    """Variable definition together with the file it was defined in."""

    path: Path
    variable: VariableDefinition
    location: Location


class ProjectDuplicationsChecker(ProjectChecker):
    """Checker for duplications that can only be found with the whole project context."""

    duplicated_variable_in_project: duplications.DuplicatedVariableInProjectRule

    def scan_project(
        self,
        project_source_file: SourceFile | VirtualSourceFile,
        config_manager: ConfigManager,  # noqa: ARG002
        context: ProjectContext,
    ) -> list[Diagnostic]:
        self.issues = []
        reported: set[tuple[Path, int, int, str]] = set()
        for project_file in context.iter_files():
            for occurrences in self._duplicated_definitions(project_file, context):
                first, *rest = occurrences
                for duplicate in rest:
                    self._report_duplicate(duplicate, first, context, project_source_file, reported)
        return self.issues

    @staticmethod
    def _duplicated_definitions(project_file: ProjectFile, context: ProjectContext) -> list[list[VariableOccurrence]]:
        """
        Find variables defined more than once in files visible from given file.

        Returns:
            List of duplicated occurrences, each sorted by source path and line number.

        """
        by_name: dict[str, list[VariableOccurrence]] = defaultdict(list)
        for visible_file in context.imported_files(project_file.path):
            for variable in visible_file.variables:
                if variable.location is not None:
                    by_name[variable.normalized_name].append(
                        VariableOccurrence(visible_file.path, variable, variable.location)
                    )
        return [
            sorted(occurrences, key=lambda item: (str(item.path), item.location.lineno))
            for occurrences in by_name.values()
            if len({occurrence.path for occurrence in occurrences}) > 1
        ]

    def _report_duplicate(
        self,
        duplicate: VariableOccurrence,
        first: VariableOccurrence,
        context: ProjectContext,
        project_source_file: SourceFile | VirtualSourceFile,
        reported: set[tuple[Path, int, int, str]],
    ) -> None:
        if duplicate.path == first.path:
            return
        location = duplicate.location
        key = (duplicate.path, location.lineno, location.col, duplicate.variable.normalized_name)
        if key in reported:
            return
        reported.add(key)
        self.report(
            self.duplicated_variable_in_project,
            source=SourceFile(path=duplicate.path, config=project_source_file.config),
            name=duplicate.variable.name,
            first_source=relative_path(first.path, context.root),
            first_occurrence_line=first.location.lineno,
            lineno=location.lineno,
            col=location.col,
            end_lineno=location.end_lineno,
            end_col=location.end_col,
        )


def relative_path(path: Path, root: Path) -> str:
    """
    Return path relative to the project root, if possible.

    Returns:
        Relative path as string, or the absolute path if it is outside of the root.

    """
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)
