"""Checkers for the rules defined in ``robocop.linter.rules.errors``."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import Rule, VisitorChecker, arguments, errors, whitespace
from robocop.linter.utils.misc import find_robot_vars
from robocop.version_handling import ROBOT_VERSION, TEST_METADATA_SUPPORTED

try:
    from robot.api.parsing import If
except ImportError:
    If = None

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model.blocks import InvalidSection, NestedBlock
    from robot.parsing.model.statements import KeywordCall, Node, Statement


class ParsingErrorChecker(VisitorChecker):
    """Checker that parses Robot Framework DataErrors."""

    parsing_error: errors.ParsingErrorRule
    invalid_continuation_mark: errors.InvalidContinuationMarkRule
    not_enough_whitespace_after_newline_marker: whitespace.NotEnoughWhitespaceAfterNewlineMarkerRule
    invalid_argument: arguments.InvalidArgumentsRule
    non_existing_setting: errors.NonExistingSettingRule
    setting_not_suported: errors.SettingNotSupportedRule
    not_enough_whitespace_after_variable: whitespace.NotEnoughWhitespaceAfterVariableRule
    not_enough_whitespace_after_suite_setting: whitespace.NotEnoughWhitespaceAfterSuiteSettingRule
    invalid_for_loop: errors.InvalidForLoopRule
    invalid_if: errors.InvalidIfRule
    return_in_test_case: errors.ReturnInTestCaseRule
    invalid_section_in_resource: errors.InvalidSectionInResourceRule
    invalid_setting_in_resource: errors.InvalidSettingInResourceRule
    unsupported_setting_in_ini_file: errors.UnsupportedSettingInIniFileRule

    keyword_only_settings: set[str] = {"Arguments", "Return"}
    keyword_settings = [
        "[Documentation]",
        "[Tags]",
        "[Arguments]",
        "[Return]",
        "[Teardown]",
        "[Timeout]",
    ]
    # ``[Metadata]`` is only allowed in test cases and only since Robot Framework 7.5
    test_case_only_settings = {"Setup", "Template"} | ({"Metadata"} if TEST_METADATA_SUPPORTED else set())
    test_case_settings = [
        "[Documentation]",
        *(["[Metadata]"] if TEST_METADATA_SUPPORTED else []),
        "[Tags]",
        "[Setup]",
        "[Teardown]",
        "[Template]",
        "[Timeout]",
    ]
    suite_settings = {
        "documentation": "Documentation",
        "suitesetup": "Suite Setup",
        "suiteteardown": "Suite Teardown",
        "metadata": "Metadata",
        "testsetup": "Test Setup",
        "testteardown": "Test Teardown",
        "testtemplate": "Test Template",
        "testtimeout": "Test Timeout",
        "forcetags": "Force Tags",
        "defaulttags": "Default Tags",
        "library": "Library",
        "resource": "Resource",
        "variables": "Variables",
    }
    ignore_errors = (
        "can only be used inside a loop",
        "is allowed only once. Only the first value is used",
        "Test name cannot be empty",  # handled by test-case-name-is-empty
        "User keyword name cannot be empty",  # handled by keyword-name-is-empty
        "END is not allowed in this context",  # handled by statement-outside-loop
    )

    def __init__(self) -> None:
        super().__init__()
        self.in_block = None

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_If(self, node: NestedBlock) -> None:  # noqa: N802
        self.in_block = node  # to ensure we're in IF for `invalid-if` rule
        self.parse_errors(node)
        self.generic_visit(node)

    visit_For = visit_While = visit_Try = visit_If  # noqa: N815

    def visit_Group(self, node: NestedBlock) -> None:  # noqa: N802
        # Report block level errors such as ``GROUP cannot be empty.`` or ``GROUP must have closing END.``.
        # Unlike IF/FOR/WHILE/TRY, we must not set ``self.in_block`` (it is only used for the ``invalid-if`` rule).
        self.parse_errors(node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if node.keyword and node.keyword.startswith("..."):
            col = node.data_tokens[0].col_offset + 1
            self.report(
                self.not_enough_whitespace_after_newline_marker,
                name_end_col=col + 3,
                node=node,
                col=col,
                end_col=col + 3,
            )
        self.generic_visit(node)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        self.parse_errors(node)

    def visit_InvalidSection(self, node: InvalidSection) -> None:  # noqa: N802
        invalid_header = node.header.get_token(Token.INVALID_HEADER)
        if "Resource file with" in invalid_header.error:
            section_name = invalid_header.value
            self.report(
                self.invalid_section_in_resource,
                section_name=section_name,
                node=node,
                end_col=node.col_offset + len(section_name) + 1,
            )

    def parse_errors(self, node: Node) -> None:
        if node is None:
            return
        for index, error in enumerate(node.errors):
            self.handle_error(node, error, error_index=index)

    def handle_error(self, node: Node, error: str, error_index: int = 0) -> None:
        if not error:
            return
        if any(should_ignore in error for should_ignore in self.ignore_errors):
            return
        if "Invalid argument syntax" in error:
            self.handle_invalid_syntax(node, error)
        elif "is not allowed with" in error:
            self.handle_not_allowed_setting(node, error)
        elif "Non-existing setting" in error:
            self.handle_invalid_setting(node, error)
        elif "Invalid variable name" in error:
            self.handle_invalid_variable(node, error)
        elif "RETURN can only be used inside" in error or "RETURN is not allowed in this context" in error:
            token = node.data_tokens[0]
            self.report(self.return_in_test_case, node=node, col=token.col_offset + 1, end_col=token.end_col_offset + 1)
        elif "IF" in error or ("ELSE" in error and If and isinstance(self.in_block, If)):
            self.handle_invalid_block(node, error, self.invalid_if)
        elif "FOR loop" in error:
            self.handle_invalid_block(node, error, self.invalid_for_loop)
        elif "Non-default argument after default arguments" in error or "Only last argument can be kwargs" in error:
            self.handle_positional_after_named(node, error_index)
        elif "Resource file with" in error:
            self.handle_invalid_section_in_resource(node)
        elif "is not allowed in resource file" in error:
            self.handle_invalid_setting_in_resource_file(node, error)
        elif "is not allowed in suite initialization file" in error:
            self.handle_unsupported_settings_in_init_file(node)
        else:
            error = error.replace("\n   ", "")
            error_node = node.header if hasattr(node, "header") else node
            start_col = error_node.data_tokens[0].col_offset + 1
            end_col = error_node.col_offset + len(node.name) if hasattr(node, "name") else error_node.end_col_offset
            self.report(self.parsing_error, error_msg=error, node=node, col=start_col, end_col=end_col)

    def handle_invalid_block(self, node: Node, error: str, block_name: Rule) -> None:
        if hasattr(node, "header"):
            token = node.header.get_token(node.header.type)
        else:
            token = node.get_token(node.type)
        self.report(
            block_name,
            error_msg=error.replace("Robot Framework syntax error: ", "")[:-1],
            node=token,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )

    def handle_invalid_syntax(self, node: Node, error: str) -> None:
        # robot doesn't report on exact token, so we need to find it
        match = re.search("'(.+)'", error)
        if not match:
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            value, *_ = arg.value.split("=", maxsplit=1)
            if value == match.group(1):
                col = arg.col_offset + 1
                end_col = arg.end_col_offset + 1
                self.report(self.invalid_argument, error_msg=error[:-1], node=arg, col=col, end_col=end_col)
                return
        self.report(self.parsing_error, error_msg=error, node=node)

    def handle_not_allowed_setting(self, node: Node, error: str) -> None:
        """
        Report settings that are not allowed in the Test Case or Keyword.

        Since Robot Framework 6 settings that are not allowed in Test/Keyword are reported with separate error
        message rather than with 'Non-existing setting'.
        """
        error_match = re.search("Setting '(.*)' is not allowed", error)
        if not error_match:
            return
        setting_error = error_match.group(1)
        if not setting_error:
            return
        token = node.data_tokens[0]
        if "with tests" in error:
            node_name = "Test Case or Task"
            allowed_settings = ", ".join(self.test_case_settings)
        elif "keywords" in error:
            node_name = "Keyword"
            allowed_settings = ", ".join(self.keyword_settings)
        else:
            return
        self.report(
            self.setting_not_suported,
            setting_name=setting_error,
            test_or_keyword=node_name,
            allowed_settings=allowed_settings,
            node=node,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )

    def handle_invalid_setting(self, node: Node, error: str) -> None:
        error_match = re.search("Non-existing setting '(.*)'.", error)
        if not error_match:
            return
        setting_error = error_match.group(1)
        if not setting_error:
            return
        token = node.data_tokens[0]
        if setting_error.lstrip().startswith(".."):
            self.handle_invalid_continuation_mark(node, token.value)
        elif setting_error in self.keyword_only_settings:
            self.report(
                self.setting_not_suported,
                setting_name=setting_error,
                test_or_keyword="Test Case or Task",  # TODO: Recognize if it is inside Task
                allowed_settings=", ".join(self.test_case_settings),
                node=node,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )
        elif setting_error in self.test_case_only_settings:
            self.report(
                self.setting_not_suported,
                setting_name=setting_error,
                test_or_keyword="Keyword",
                allowed_settings=", ".join(self.keyword_settings),
                node=node,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )
        else:
            suite_sett_cand = node.data_tokens[0].value.replace(" ", "").lower()
            for setting in self.suite_settings:
                if suite_sett_cand.startswith(setting):
                    if setting_error[0].strip():  # filter out "suite-setting-should-be-left-aligned"
                        token = node.data_tokens[0]
                        self.report(
                            self.not_enough_whitespace_after_suite_setting,
                            setting_name=self.suite_settings[setting],
                            name_end_col=self.get_setting_name_end_col(token.value, setting, token.col_offset),
                            node=token,
                            end_col=token.end_col_offset + 1,
                        )
                    return
            error = error.replace("\n   ", "").replace("Robot Framework syntax error: ", "")
            error = error.removesuffix(".")
            self.report(
                self.non_existing_setting,
                error_msg=error,
                node=node,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )

    def handle_invalid_variable(self, node: Node, error: str) -> None:
        var_error = re.search("Invalid variable name '(.*)'.", error)
        if not var_error or not var_error.group(1):  # empty variable name due to invalid parsing
            return
        if var_error.group(1).lstrip().startswith(".."):
            self.handle_invalid_continuation_mark(node, var_error.group(1))
        elif not var_error.group(1)[0].strip():  # not left aligned variable
            return
        else:
            variable_token = node.get_token(Token.VARIABLE)
            variables = find_robot_vars(variable_token.value) if variable_token else None
            if variables and variables[0][0] == 0:
                self.report(
                    self.not_enough_whitespace_after_variable,
                    variable_name=variable_token.value,
                    name_end_col=variable_token.col_offset + variables[0][1] + 1,
                    node=variable_token,
                    col=variable_token.col_offset + 1,
                    end_col=variable_token.end_col_offset + 1,
                )
            else:
                error = error.replace("\n   ", "")
                self.report(self.parsing_error, error_msg=error, node=node)

    def handle_invalid_continuation_mark(self, node: Node, name: str) -> None:
        stripped = name.lstrip()
        if len(stripped) == 2 or not stripped[2].strip():
            first_dot = name.find(".") + 1
            self.report(self.invalid_continuation_mark, mark=stripped, node=node, col=first_dot, end_col=first_dot + 2)
        elif len(stripped) >= 4:
            if stripped[:4] == "....":
                first_dot = name.find(".") + 1
                self.report(
                    self.invalid_continuation_mark, mark=stripped, node=node, col=first_dot, end_col=first_dot + 4
                )
            else:  # '... ' or '...value' or '...\t'
                col = name.find(".") + 1
                self.report(
                    self.not_enough_whitespace_after_newline_marker,
                    name_end_col=col + 3,
                    node=node,
                    col=col,
                    end_col=col + 3,
                )

    @staticmethod
    def get_setting_name_end_col(value: str, normalized_setting: str, col_offset: int) -> int:
        """Return the first column after a setting name, accounting for internal spaces."""
        remaining = len(normalized_setting)
        for index, char in enumerate(value):
            if not char.isspace():
                remaining -= 1
                if remaining == 0:
                    return col_offset + index + 2
        return col_offset + len(value) + 1

    def handle_unsupported_settings_in_init_file(self, node: Node) -> None:
        if ROBOT_VERSION.major < 6 and "__init__" not in self.source_file.path.name:
            return  # handle bug where Robot reports invalid setting as not allowed in suite init file
        setting_node = node.data_tokens[0]
        setting_name = setting_node.value
        self.report(
            self.unsupported_setting_in_ini_file,
            setting=setting_name,
            node=setting_node,
            col=setting_node.col_offset + 1,
            end_col=setting_node.col_offset + 1 + len(setting_name),
            lineno=setting_node.lineno,
        )

    @staticmethod
    def is_var_positional(value: str) -> bool:
        return bool(value) and (value.startswith("&") or "=" in value)

    def handle_positional_after_named(self, node: Node, error_index: int) -> None:
        """
        Robot Framework reports all errors on parent node.

        That's why we need to find which token is invalid - and in
        case there are several invalid tokens we need to skip tokens that were already reported for particular node.
        """
        named_found = False
        token = node
        skip = error_index
        for token in node.get_tokens(Token.ARGUMENT):
            if named_found and not self.is_var_positional(token.value):
                if not skip:
                    break
                skip -= 1
            named_found = self.is_var_positional(token.value)
        self.report(
            self.parsing_error,
            error_msg=f"Positional argument '{token.value}' follows named argument",
            node=token,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )

    def handle_invalid_section_in_resource(self, node: Node) -> None:
        error_token = node.tokens[0]
        section_name = error_token.value
        self.report(
            self.invalid_section_in_resource,
            section_name=section_name,
            node=node,
            end_col=node.col_offset + len(section_name) + 1,
        )

    def handle_invalid_setting_in_resource_file(self, node: Node, error: str) -> None:
        setting_error = re.search("Setting '(.*)' is not allowed in resource file", error)
        if setting_error:
            self.report(
                self.invalid_setting_in_resource,
                section_name=setting_error.group(1),
                node=node,
                lineno=node.lineno,
                end_col=node.end_col_offset,
            )
