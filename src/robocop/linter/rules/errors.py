"""Errors checkers"""

import re

from robot.api import Token

try:
    from robot.api.parsing import If
except ImportError:
    If = None

from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker, arguments, whitespace
from robocop.linter.utils import ROBOT_VERSION, find_robot_vars


class ParsingErrorRule(Rule):  # TODO docs
    name = "parsing-error"
    rule_id = "ERR01"
    message = "Robot Framework syntax error: {error_msg}"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"


class MissingKeywordNameRule(Rule):
    """
    Missing keyword name.

    Example of rule violation::

        *** Keywords ***
        Keyword
            ${var}
            ${one}      ${two}

    """

    name = "missing-keyword-name"
    rule_id = "ERR03"
    message = "Missing keyword name when calling some values"
    severity = RuleSeverity.ERROR
    added_in_version = "1.8.0"


class VariablesImportWithArgsRule(Rule):
    """
    YAML variables file import with arguments.

    Example of rule violation::

        *** Settings ***
        Variables    vars.yaml        arg1
        Variables    variables.yml    arg2
        Variables    module           arg3  # valid from RF > 5

    """

    name = "variables-import-with-args"
    rule_id = "ERR04"
    message = "YAML variable files do not take arguments"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class InvalidContinuationMarkRule(Rule):
    """
    Invalid continuation mark.

    Example of rule violation::

        Keyword
        ..  ${var}  # .. instead of ...
        ...  1
        ....  2  # .... instead of ...

    """

    name = "invalid-continuation-mark"
    rule_id = "ERR05"
    message = "Invalid continuation mark '{mark}'. It should be '...'"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class NonExistingSettingRule(Rule):
    """
    Non-existing setting used in the code.

    Example of rule violation::

       *** Test Cases ***
       Test case
           [Not Existing]  arg
           [Arguments]  ${arg}

    """

    name = "non-existing-setting"
    rule_id = "ERR08"
    message = "{error_msg}"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class SettingNotSupportedRule(Rule):
    """
    Not supported setting.

    Following settings are supported in Test Case or Task::

        *** Test Cases ***
        Test case
            [Documentation]	 Used for specifying a test case documentation.
            [Tags]	         Used for tagging test cases.
            [Setup]	         Used for specifying a test setup.
            [Teardown]	     Used for specifying a test teardown.
            [Template]	     Used for specifying a template keyword.
            [Timeout]	     Used for specifying a test case timeout.

    Following settings are supported in Keyword::

        *** Keywords ***
        Keyword
            [Documentation]	 Used for specifying a user keyword documentation.
            [Tags]	         Used for specifying user keyword tags.
            [Arguments]	     Used for specifying user keyword arguments.
            [Return]	     Used for specifying user keyword return values.
            [Teardown]	     Used for specifying user keyword teardown.
            [Timeout]	     Used for specifying a user keyword timeout.

    """

    name = "setting-not-supported"
    rule_id = "ERR09"
    message = "Setting '[{setting_name}]' is not supported in {test_or_keyword}. Allowed are: {allowed_settings}"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class InvalidForLoopRule(Rule):
    """Invalid FOR loop syntax."""

    name = "invalid-for-loop"
    rule_id = "ERR12"
    message = "Invalid for loop syntax: {error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.0.0"


class InvalidIfRule(Rule):
    """Invalid IF syntax."""

    name = "invalid-if"
    rule_id = "ERR13"
    message = "Invalid IF syntax: {error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.0.0"


class ReturnInTestCaseRule(Rule):
    """RETURN used outside user keyword."""

    name = "return-in-test-case"
    rule_id = "ERR14"
    message = "RETURN can only be used inside a user keyword"
    severity = RuleSeverity.ERROR
    version = ">=5.0"
    added_in_version = "2.0.0"


class InvalidSectionInResourceRule(Rule):
    """
    Resource file with not supported section.

    The higher-level structure of resource files is the same as that of test case files,
    but they can't contain Test Cases or Tasks sections.

    """

    name = "invalid-section-in-resource"
    rule_id = "ERR15"
    message = "Resource file can't contain '{section_name}' section"
    severity = RuleSeverity.ERROR
    added_in_version = "3.1.0"


class InvalidSettingInResourceRule(Rule):
    """
    Not supported setting in ``*** Settings ***`` section in a resource file.

    The Setting section in resource files can contain only import settings (``Library``,
    ``Resource``, ``Variables``), ``Documentation`` and ``Keyword Tags``.
    """

    name = "invalid-setting-in-resource"
    rule_id = "ERR16"
    message = "Settings section in resource file can't contain '{section_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "3.3.0"


class UnsupportedSettingInIniFileRule(Rule):
    """
    Not supported setting in a initialization file.

    Settings ``Default Tags`` and ``Test Template`` are not supported in initialization files.
    """

    name = "unsupported-setting-in-init-file"
    rule_id = "ERR17"
    message = "Setting '{setting}' is not supported in initialization files"
    severity = RuleSeverity.ERROR
    added_in_version = "3.3.0"


class ParsingErrorChecker(VisitorChecker):
    """Checker that parses Robot Framework DataErrors."""

    parsing_error: ParsingErrorRule
    invalid_continuation_mark: InvalidContinuationMarkRule
    not_enough_whitespace_after_newline_marker: whitespace.NotEnoughWhitespaceAfterNewlineMarkerRule
    invalid_argument: arguments.InvalidArgumentsRule
    non_existing_setting: NonExistingSettingRule
    setting_not_suported: SettingNotSupportedRule
    not_enough_whitespace_after_variable: whitespace.NotEnoughWhitespaceAfterVariableRule
    not_enough_whitespace_after_suite_setting: whitespace.NotEnoughWhitespaceAfterSuiteSettingRule
    invalid_for_loop: InvalidForLoopRule
    invalid_if: InvalidIfRule
    return_in_test_case: ReturnInTestCaseRule
    invalid_section_in_resource: InvalidSectionInResourceRule
    invalid_setting_in_resource: InvalidSettingInResourceRule
    unsupported_setting_in_ini_file: UnsupportedSettingInIniFileRule

    keyword_only_settings: set[str] = {"Arguments", "Return"}
    keyword_settings = [
        "[Documentation]",
        "[Tags]",
        "[Arguments]",
        "[Return]",
        "[Teardown]",
        "[Timeout]",
    ]
    test_case_only_settings = {"Setup", "Template"}
    test_case_settings = [
        "[Documentation]",
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

    def __init__(self):
        super().__init__()
        self.in_block = None

    def visit_File(self, node) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_If(self, node) -> None:  # noqa: N802
        self.in_block = node  # to ensure we're in IF for `invalid-if` rule
        self.parse_errors(node)
        self.generic_visit(node)

    visit_For = visit_While = visit_Try = visit_If  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if node.keyword and node.keyword.startswith("..."):
            col = node.data_tokens[0].col_offset + 1
            self.report(self.not_enough_whitespace_after_newline_marker, node=node, col=col, end_col=col + 3)
        self.generic_visit(node)

    def visit_Statement(self, node) -> None:  # noqa: N802
        self.parse_errors(node)

    def visit_InvalidSection(self, node) -> None:  # noqa: N802
        invalid_header = node.header.get_token(Token.INVALID_HEADER)
        if "Resource file with" in invalid_header.error:
            section_name = invalid_header.value
            self.report(
                self.invalid_section_in_resource,
                section_name=section_name,
                node=node,
                end_col=node.col_offset + len(section_name) + 1,
            )

    def parse_errors(self, node) -> None:
        if node is None:
            return
        if ROBOT_VERSION.major != 3:
            for index, error in enumerate(node.errors):
                self.handle_error(node, error, error_index=index)
        else:
            self.handle_error(node, node.error)

    def handle_error(self, node, error, error_index=0) -> None:
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

    def handle_invalid_block(self, node, error, block_name) -> None:
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

    def handle_invalid_syntax(self, node, error) -> None:
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

    def handle_not_allowed_setting(self, node, error) -> None:
        """
        Since Robot Framework 6 settings that are not allowed in Test/Keyword are reported with separate error
        message rather than with 'Non-existing setting'.
        """
        setting_error = re.search("Setting '(.*)' is not allowed", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
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

    def handle_invalid_setting(self, node, error) -> None:
        setting_error = re.search("Non-existing setting '(.*)'.", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
        if not setting_error:
            return
        token = node.data_tokens[0]
        if setting_error.lstrip().startswith(".."):
            self.handle_invalid_continuation_mark(node, token.value)
        elif setting_error in self.keyword_only_settings:
            self.report(
                self.setting_not_suported,
                setting_name=setting_error,
                test_or_keyword="Test Case",  # TODO: Recognize if it is inside Task
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

    def handle_invalid_variable(self, node, error) -> None:
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
                    node=variable_token,
                    col=variable_token.col_offset + 1,
                    end_col=variable_token.end_col_offset + 1,
                )
            else:
                error = error.replace("\n   ", "")
                self.report(self.parsing_error, error_msg=error, node=node)

    def handle_invalid_continuation_mark(self, node, name) -> None:
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
                    node=node,
                    col=col,
                    end_col=col + 3,
                )

    def handle_unsupported_settings_in_init_file(self, node) -> None:
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
    def is_var_positional(value):
        return value and (value.startswith("&") or "=" in value)

    def handle_positional_after_named(self, node, error_index) -> None:
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

    def handle_invalid_section_in_resource(self, node) -> None:
        error_token = node.tokens[0]
        section_name = error_token.value
        self.report(
            self.invalid_section_in_resource,
            section_name=section_name,
            node=node,
            end_col=node.col_offset + len(section_name) + 1,
        )

    def handle_invalid_setting_in_resource_file(self, node, error) -> None:
        setting_error = re.search("Setting '(.*)' is not allowed in resource file", error)
        self.report(
            self.invalid_setting_in_resource,
            section_name=setting_error.group(1),
            node=node,
            lineno=node.lineno,
            end_col=node.end_col_offset + 1,
        )


class TwoSpacesAfterSettingsChecker(VisitorChecker):
    """Checker for not enough whitespaces after [Setting] header."""

    not_enough_whitespace_after_setting: whitespace.NotEnoughWhitespaceAfterSettingRule

    def __init__(self):
        self.headers = {
            "arguments",
            "documentation",
            "setup",
            "timeout",
            "teardown",
            "template",
            "tags",
        }
        self.setting_pattern = re.compile(r"\[\s?(\w+)\s?\]")
        super().__init__()

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        """Invalid settings like '[Arguments] ${var}' will be parsed as keyword call"""
        if not node.keyword:
            return

        match = self.setting_pattern.match(node.keyword)
        if not match:
            return
        if match.group(1).lower() in self.headers:
            self.report(
                self.not_enough_whitespace_after_setting,
                setting_name=match.group(0),
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
            )


class MissingKeywordName(VisitorChecker):  # TODO should be part of other checker
    """Checker for missing keyword name."""

    missing_keyword_name: MissingKeywordNameRule

    def visit_File(self, node) -> None:  # noqa: N802
        self.generic_visit(node)

    def visit_EmptyLine(self, node) -> None:  # noqa: N802
        if ROBOT_VERSION.major < 5:
            return
        assign_token = node.get_token(Token.ASSIGN)
        if assign_token:
            self.report(
                self.missing_keyword_name,
                node=node,
                lineno=node.lineno,
                col=assign_token.col_offset + 1,
            )

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if not node.keyword:
            self.report(
                self.missing_keyword_name,
                node=node,
                lineno=node.lineno,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
            )


class VariablesImportErrorChecker(VisitorChecker):  # TODO merge such visitors into one
    """Checker for syntax error in variables import."""

    variables_import_with_args: VariablesImportWithArgsRule

    def visit_VariablesImport(self, node) -> None:  # noqa: N802
        if node.name and node.name.endswith((".yaml", ".yml")) and node.get_token(Token.ARGUMENT):
            eol = node.get_token(Token.EOL) or node
            self.report(self.variables_import_with_args, node=node, end_col=eol.end_col_offset)
