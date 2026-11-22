"""Checker for rules triggered by variable definitions and assignments."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import VisitorChecker, misc, typing, variables
from robocop.linter.utils import misc as utils

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.blocks import For, KeywordSection, TestCaseSection, VariableSection
    from robot.parsing.model.statements import Arguments, KeywordCall, Var, Variable


class VariablesChecker(VisitorChecker):
    """Checker for rules reported for variable definitions, assignments and their scopes."""

    empty_variable: variables.EmptyVariableRule
    no_global_variable: variables.NoGlobalVariableRule
    no_suite_variable: variables.NoSuiteVariableRule
    no_test_variable: variables.NoTestVariableRule
    set_keyword_with_type: typing.SetKeywordWithTypeRule
    missing_section_variable_type: typing.MissingSectionVariableTypeRule
    missing_keyword_variable_type: typing.MissingKeywordVariableTypeRule
    missing_test_variable_type: typing.MissingTestVariableTypeRule
    missing_argument_type: typing.MissingArgumentTypeRule
    missing_for_loop_variable_type: typing.MissingForLoopVariableTypeRule
    inconsistent_assignment: misc.InconsistentAssignmentRule
    inconsistent_assignment_in_variables: misc.InconsistentAssignmentInVariablesRule

    set_variable_keywords = {
        "setglobalvariable",
        "setsuitevariable",
        "settestvariable",
        "settaskvariable",
        "setlocalvariable",
    }

    def __init__(self) -> None:
        self.keyword_expected_sign_type: str | None = None
        self.variables_expected_sign_type: str | None = None
        self.check_empty_variable = True
        self.missing_body_variable_type: (
            typing.MissingKeywordVariableTypeRule | typing.MissingTestVariableTypeRule | None
        ) = None
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.check_empty_variable = True
        self.missing_body_variable_type = None
        self.detect_assignment_sign(node)
        self.generic_visit(node)

    def detect_assignment_sign(self, node: File) -> None:
        """Find the most common assignment sign in the file if the rules are set to autodetect it."""
        self.keyword_expected_sign_type = self.inconsistent_assignment.assignment_sign_type
        self.variables_expected_sign_type = self.inconsistent_assignment_in_variables.assignment_sign_type
        if "autodetect" not in (self.keyword_expected_sign_type, self.variables_expected_sign_type):
            return
        auto_detector = utils.AssignmentTypeDetector()
        auto_detector.visit(node)
        if self.keyword_expected_sign_type == "autodetect":
            self.keyword_expected_sign_type = auto_detector.keyword_most_common
        if self.variables_expected_sign_type == "autodetect":
            self.variables_expected_sign_type = auto_detector.variables_most_common

    def visit_VariableSection(self, node: VariableSection) -> None:  # noqa: N802
        if self.variables_expected_sign_type is not None:
            self.inconsistent_assignment_in_variables.check(node, self.variables_expected_sign_type)
        # ``empty-variable`` is only reported here when the variables section is one of its configured sources
        self.check_empty_variable = "section" in self.empty_variable.variable_source
        self.generic_visit(node)
        self.check_empty_variable = True

    def visit_KeywordSection(self, node: KeywordSection) -> None:  # noqa: N802
        self.visit_body_section(node, self.missing_keyword_variable_type)

    def visit_TestCaseSection(self, node: TestCaseSection) -> None:  # noqa: N802
        self.visit_body_section(node, self.missing_test_variable_type)

    def visit_body_section(
        self,
        node: KeywordSection | TestCaseSection,
        missing_type_rule: typing.MissingKeywordVariableTypeRule | typing.MissingTestVariableTypeRule,
    ) -> None:
        # ``empty-variable`` is only reported here when the VAR syntax is one of its configured sources
        self.check_empty_variable = "var" in self.empty_variable.variable_source
        self.missing_body_variable_type = missing_type_rule
        self.generic_visit(node)
        self.check_empty_variable = True
        self.missing_body_variable_type = None

    def check_body_variable_type(self, node: Var | KeywordCall, token: Token) -> None:
        if self.missing_body_variable_type is not None:
            self.missing_body_variable_type.check(node, token)

    def visit_Variable(self, node: Variable) -> None:  # noqa: N802
        if self.check_empty_variable:
            self.empty_variable.check_variable(node)
        if node.errors:
            return
        self.missing_section_variable_type.check(node, node.data_tokens[0])

    def visit_Var(self, node: Var) -> None:  # noqa: N802
        """Visit VAR syntax introduced in Robot Framework 7. Is ignored in Robot < 7."""
        if self.check_empty_variable:
            self.empty_variable.check_var(node)
        self.check_var_scope(node)
        if node.errors:
            return
        variable = node.get_token(Token.VARIABLE)
        if variable:
            self.check_body_variable_type(node, variable)
            self.check_var_assignment_sign(variable)

    def check_var_assignment_sign(self, variable: Token) -> None:
        if self.keyword_expected_sign_type is None:
            return
        self.inconsistent_assignment.check(variable, self.keyword_expected_sign_type)

    def check_var_scope(self, node: Var) -> None:
        if not node.scope:
            return
        scope = node.scope.upper()
        if scope == "LOCAL":
            return
        option_token = node.get_token(Token.OPTION)
        if scope == "GLOBAL":
            self.no_global_variable.check(option_token)
        elif scope in ("SUITE", "SUITES"):
            self.no_suite_variable.check(option_token)
        elif scope in ("TEST", "TASK"):
            self.no_test_variable.check(option_token)
        # Unexpected scope, or variable-defined scope

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        self.check_assignment_sign(node)
        for token in node.get_tokens(Token.ASSIGN):
            self.check_body_variable_type(node, token)
        self.check_set_variable_keyword(node)

    def check_assignment_sign(self, node: KeywordCall) -> None:
        if self.keyword_expected_sign_type is None or not node.keyword or not node.assign:
            return
        assign_tokens = node.get_tokens(Token.ASSIGN)
        self.inconsistent_assignment.check(assign_tokens[-1], self.keyword_expected_sign_type)

    def check_set_variable_keyword(self, node: KeywordCall) -> None:
        keyword_token = node.get_token(Token.KEYWORD)
        if not keyword_token:
            return
        keyword_name = utils.normalize_robot_name(keyword_token.value, remove_prefix="builtin.")
        if keyword_name not in self.set_variable_keywords:
            return
        self.set_keyword_with_type.check(node)
        if keyword_name == "setglobalvariable":
            self.no_global_variable.check(keyword_token)
        elif keyword_name == "setsuitevariable":
            self.no_suite_variable.check(keyword_token)
        elif keyword_name in ("settestvariable", "settaskvariable"):
            self.no_test_variable.check(keyword_token)

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        self.missing_argument_type.check(node)

    def visit_For(self, node: For) -> None:  # noqa: N802
        self.missing_for_loop_variable_type.check(node)
        self.generic_visit(node)  # Continue to nested loops
