"""
Whitespace rules.

Holds rules that are used outside spacing module for now - after redesign to seperate rules/checkers spacing rules
can be moved here.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from robocop.linter import sonar_qube
from robocop.linter.rules import Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.statements import KeywordCall


class NotEnoughWhitespaceAfterSettingRule(Rule):
    """
    Not enough whitespace after setting.

    Provide at least two spaces after setting.

    Incorrect code example:

        *** Test Cases ***
        Test
            [Documentation] doc
            Keyword

        *** Keywords ***
        Keyword
            [Documentation]  This is doc
            [Arguments] ${var}
            Should Be True  ${var}

    Correct code:

        *** Test Cases ***
        Test
            [Documentation]  doc
            Keyword

        *** Keywords ***
        Keyword
            [Documentation]  This is doc
            [Arguments]    ${var}
            Should Be True  ${var}

    """

    name = "not-enough-whitespace-after-setting"
    rule_id = "SPC19"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0402",)

    headers: ClassVar[set[str]] = {
        "arguments",
        "documentation",
        "setup",
        "timeout",
        "teardown",
        "template",
        "tags",
    }
    setting_pattern = re.compile(r"\[\s?(\w+)\s?\]")

    def check(self, node: KeywordCall) -> None:
        """Invalid settings like '[Arguments] ${var}' will be parsed as keyword call."""
        if not self.enabled:
            return
        match = self.setting_pattern.match(node.keyword)
        if not match:
            return
        if match.group(1).lower() in self.headers:
            self.report(
                setting_name=match.group(0),
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
            )


class NotEnoughWhitespaceAfterNewlineMarkerRule(Rule):
    """
    Not enough whitespace after a newline marker.

    Provide at least two spaces after a newline marker.

    Incorrect code example:

        *** Variables ***
        @{LIST}  1
        ... 2
        ...  3

    Correct code:

        *** Variables ***
        @{LIST}  1
        ...  2
        ...  3

    """

    name = "not-enough-whitespace-after-newline-marker"
    rule_id = "SPC20"
    message = "Not enough whitespace after '...' marker"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0406",)


class NotEnoughWhitespaceAfterVariableRule(Rule):
    """
    Not enough whitespace after variable.

    Provide at least two spaces after the variable name.

    Incorrect code example:

        *** Variables ***
        ${variable} 1
        ${other_var}  2

    Correct code:

        *** Variables ***
        ${variable}  1
        ${other_var}  2

    """

    name = "not-enough-whitespace-after-variable"
    rule_id = "SPC21"
    message = "Not enough whitespace after '{variable_name}' variable name"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0410",)


class NotEnoughWhitespaceAfterSuiteSettingRule(Rule):
    """
    Not enough whitespace after suite setting.

    Provide at least two spaces after the suite setting.

    Incorrect code example:

        *** Settings ***
        Library Collections
        Test Tags  tag
        ...  tag2
        Suite Setup Keyword

    Correct code:

        *** Settings ***
        Library    Collections
        Test Tags  tag
        ...  tag2
        Suite Setup    Keyword

    """

    name = "not-enough-whitespace-after-suite-setting"
    rule_id = "SPC22"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0411",)
