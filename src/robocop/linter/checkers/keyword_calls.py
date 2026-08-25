"""Checker for rules triggered by keyword calls and keyword-name-like settings."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import VisitorChecker, arguments, deprecated, errors, keywords, lengths, whitespace
from robocop.linter.utils.misc import normalize_robot_name
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.blocks import For
    from robot.parsing.model.statements import EmptyLine, KeywordCall, Node, Return, Setup, Template


class KeywordCallChecker(VisitorChecker):
    """Checker for rules reported for keyword calls and keyword names used in the settings."""

    sleep_keyword_used: keywords.SleepKeywordUsedRule
    not_allowed_keyword: keywords.NotAllowedKeywordRule
    number_of_returned_values: lengths.NumberOfReturnedValuesRule
    missing_keyword_name: errors.MissingKeywordNameRule
    not_enough_whitespace_after_setting: whitespace.NotEnoughWhitespaceAfterSettingRule
    deprecated_run_keyword_if: deprecated.DeprecatedRunKeywordIfRule
    deprecated_loop_keyword: deprecated.DeprecatedLoopKeywordRule
    deprecated_return_keyword: deprecated.DeprecatedReturnKeyword
    replace_set_variable_with_var: deprecated.ReplaceSetVariableWithVarRule
    replace_create_with_var: deprecated.ReplaceCreateWithVarRule
    undefined_argument_value: arguments.UndefinedArgumentValueRule

    def __init__(self) -> None:
        self.loops = 0
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.loops = 0
        self.generic_visit(node)

    def visit_For(self, node: For) -> None:  # noqa: N802
        self.loops += 1
        self.generic_visit(node)
        self.loops -= 1

    visit_While = visit_ForLoop = visit_For  # noqa: N815

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        self.missing_keyword_name.check(node)
        self.undefined_argument_value.check(node)
        # not allowed keyword is also checked for nested run keywords, even if the keyword name is empty
        self.not_allowed_keyword.check(node, Token.KEYWORD)
        if not node.keyword:  # keyword name can be empty if the syntax is invalid
            return
        self.not_enough_whitespace_after_setting.check(node)
        # Robot Framework ignores a case, underscores and whitespace when searching for keywords
        # It will match sleep, Sleep, BuiltIn.Sleep or S_leep. That's why we need to normalize name first
        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
        self.sleep_keyword_used.check(node, normalized_name)
        self.number_of_returned_values.check_keyword_call(node, normalized_name)
        self.check_if_keyword_is_deprecated(node.keyword, node, normalized_name, in_loop=self.loops > 0)
        self.check_keyword_can_be_replaced_with_var(node.keyword, node, normalized_name)

    def visit_Setup(self, node: Setup) -> None:  # noqa: N802
        self.not_allowed_keyword.check(node, Token.NAME)
        if node.name:
            self.check_if_keyword_is_deprecated(
                node.name, node, normalize_robot_name(node.name, remove_prefix="builtin.")
            )

    visit_TestSetup = visit_SuiteSetup = visit_Teardown = visit_TestTeardown = visit_SuiteTeardown = visit_Setup  # noqa: N815

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        if node.value:
            self.not_allowed_keyword.check_keyword_name(node.value, node.get_token(Token.NAME))
            self.check_if_keyword_is_deprecated(
                node.value, node, normalize_robot_name(node.value, remove_prefix="builtin.")
            )

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_EmptyLine(self, node: EmptyLine) -> None:  # noqa: N802
        self.missing_keyword_name.check_assign_without_keyword(node)

    def visit_Return(self, node: Return) -> None:  # noqa: N802
        self.number_of_returned_values.check(len(node.values), node)

    visit_ReturnStatement = visit_ReturnSetting = visit_Return  # noqa: N815

    def check_if_keyword_is_deprecated(
        self, keyword_name: str, node: Node, normalized_name: str, in_loop: bool = False
    ) -> None:
        if not self.deprecated_run_keyword_if.check(node, keyword_name, normalized_name):
            return
        if not self.deprecated_loop_keyword.check(node, keyword_name, normalized_name, in_loop):
            return
        self.deprecated_return_keyword.check(node, keyword_name, normalized_name)

    def check_keyword_can_be_replaced_with_var(self, keyword_name: str, node: Node, normalized_name: str) -> None:
        if ROBOT_VERSION.major < 7:
            return
        if not self.replace_set_variable_with_var.check(node, keyword_name, normalized_name):
            return
        self.replace_create_with_var.check(node, keyword_name, normalized_name)
