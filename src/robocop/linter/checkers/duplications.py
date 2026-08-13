"""Checkers for the rules defined in ``robocop.linter.rules.duplications``."""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import Rule, VisitorChecker, duplications, variables
from robocop.linter.utils.misc import (
    normalize_robot_name,
    normalize_robot_var_name,
    strip_equals_from_assignment,
)
from robocop.version_handling import TYPE_SUPPORTED

if TYPE_CHECKING:
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

    from robocop.linter.rules.duplications import NodeT


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
                if underline_whole_line:
                    end_col = duplicate.end_col_offset
                else:
                    end_col = duplicate.col_offset + len(duplicate.name) + 1
                self.report(
                    rule, name=duplicate.name, first_occurrence_line=nodes[0].lineno, node=duplicate, end_col=end_col
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
        self.generic_visit(node)

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
