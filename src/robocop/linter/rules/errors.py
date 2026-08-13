"""Errors checkers"""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from robot.parsing.model.statements import EmptyLine, KeywordCall, VariablesImport


class ParsingErrorRule(Rule):  # TODO docs
    name = "parsing-error"
    rule_id = "ERR01"
    message = "Robot Framework syntax error: {error_msg}"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class MissingKeywordNameRule(Rule):
    """
    Missing keyword name.

    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )

    def check(self, node: KeywordCall) -> None:
        if not self.enabled or node.keyword:
            return
        self.report(
            node=node,
            lineno=node.lineno,
            col=node.data_tokens[0].col_offset + 1,
            end_col=node.data_tokens[0].end_col_offset + 1,
        )

    def check_assign_without_keyword(self, node: EmptyLine) -> None:
        """Values assigned in a line without a keyword name are parsed as an empty line."""
        if not self.enabled or ROBOT_VERSION.major < 5:
            return
        assign_token = node.get_token(Token.ASSIGN)
        if assign_token:
            self.report(
                node=node,
                lineno=node.lineno,
                col=assign_token.col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
            )


class VariablesImportWithArgsRule(Rule):
    """
    YAML variables file import with arguments.

    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )

    def check(self, node: VariablesImport) -> None:
        if node.name and node.name.endswith((".yaml", ".yml")) and node.get_token(Token.ARGUMENT):
            eol = node.get_token(Token.EOL) or node
            self.report(node=node, end_col=eol.end_col_offset)


class InvalidContinuationMarkRule(Rule):
    """
    Invalid continuation mark.

    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class NonExistingSettingRule(Rule):
    """
    Non-existing setting used in the code.

    Example of rule violation:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class SettingNotSupportedRule(Rule):
    """
    Not supported setting.

    The following settings are supported in Test Case or Task:

        *** Test Cases ***
        Test case
            [Documentation]	 Used for specifying a test case documentation.
            [Tags]	         Used for tagging test cases.
            [Setup]	         Used for specifying a test setup.
            [Teardown]	     Used for specifying a test teardown.
            [Template]	     Used for specifying a template keyword.
            [Timeout]	     Used for specifying a test case timeout.

    The following settings are supported in Keyword:

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class InvalidForLoopRule(Rule):
    """Invalid FOR loop syntax."""

    name = "invalid-for-loop"
    rule_id = "ERR12"
    message = "Invalid for loop syntax: {error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class InvalidIfRule(Rule):
    """Invalid IF syntax."""

    name = "invalid-if"
    rule_id = "ERR13"
    message = "Invalid IF syntax: {error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class ReturnInTestCaseRule(Rule):
    """RETURN used outside the user keyword."""

    name = "return-in-test-case"
    rule_id = "ERR14"
    message = "RETURN can only be used inside a user keyword"
    severity = RuleSeverity.ERROR
    version = ">=5.0"
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class InvalidSectionInResourceRule(Rule):
    """
    Resource file with a not supported section.

    The higher-level structure of resource files is the same as that of test case files,
    but they can't contain Test Cases or Tasks sections.

    """

    name = "invalid-section-in-resource"
    rule_id = "ERR15"
    message = "Resource file can't contain '{section_name}' section"
    severity = RuleSeverity.ERROR
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


class InvalidSettingInResourceRule(Rule):
    """
    Not supported setting in the `` *** Settings ***`` section in a resource file.

    The Setting section in resource files can contain only import settings (``Library``,
    ``Resource``, ``Variables``), ``Documentation`` and ``Keyword Tags``.
    """

    name = "invalid-setting-in-resource"
    rule_id = "ERR16"
    message = "Settings section in resource file can't contain '{section_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "3.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )


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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
