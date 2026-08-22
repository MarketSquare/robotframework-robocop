"""
Whitespace rules.

Holds rules that are used outside spacing module for now - after redesign to seperate rules/checkers spacing rules
can be moved here.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.statements import KeywordCall

    from robocop.linter.diagnostics import Diagnostic


def expand_separator_fix(rule: FixableRule, diag: Diagnostic, source_lines: list[str]) -> Fix:
    """Replace a malformed separator after a name with the standard four spaces."""
    separator_col = diag.reported_arguments["name_end_col"]
    if not isinstance(separator_col, int):
        msg = f"Expected integer name_end_col, got {type(separator_col).__name__}"
        raise TypeError(msg)
    line = source_lines[diag.range.start.line - 1]
    separator_end_col = separator_col + 1 if line[separator_col - 1 : separator_col] in {" ", "\t"} else separator_col
    start_col = separator_col
    replacement = "    "
    canonical_name = diag.reported_arguments.get("setting_name")
    current_name = line[diag.range.start.character - 1 : separator_col - 1]
    if (
        isinstance(canonical_name, str)
        and re.sub(r"\s", "", current_name).casefold() == re.sub(r"\s", "", canonical_name).casefold()
    ):
        start_col = diag.range.start.character
        replacement = f"{canonical_name}    "
    edit = TextEdit(
        rule_id=rule.rule_id,
        rule_name=rule.name,
        start_line=diag.range.start.line,
        start_col=start_col,
        end_line=diag.range.start.line,
        end_col=separator_end_col,
        replacement=replacement,
    )
    return Fix(edits=[edit], message="Expand separator to four spaces", applicability=FixApplicability.SAFE)


class NotEnoughWhitespaceAfterSettingRule(FixableRule):
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

    The separator can be expanded automatically with the ``--fix`` option.

    """

    name = "not-enough-whitespace-after-setting"
    rule_id = "SPC19"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0402",)

    headers: ClassVar[set[str]] = {
        "arguments",
        "documentation",
        "metadata",
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
                name_end_col=node.data_tokens[0].col_offset + match.end() + 1,
                node=node,
                col=node.data_tokens[0].col_offset + 1,
                end_col=node.data_tokens[0].end_col_offset + 1,
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return expand_separator_fix(self, diag, source_lines)


class NotEnoughWhitespaceAfterNewlineMarkerRule(FixableRule):
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

    The separator can be expanded automatically with the ``--fix`` option.

    """

    name = "not-enough-whitespace-after-newline-marker"
    rule_id = "SPC20"
    message = "Not enough whitespace after '...' marker"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0406",)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return expand_separator_fix(self, diag, source_lines)


class NotEnoughWhitespaceAfterVariableRule(FixableRule):
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

    The separator can be expanded automatically with the ``--fix`` option.

    """

    name = "not-enough-whitespace-after-variable"
    rule_id = "SPC21"
    message = "Not enough whitespace after '{variable_name}' variable name"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0410",)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return expand_separator_fix(self, diag, source_lines)


class NotEnoughWhitespaceAfterSuiteSettingRule(FixableRule):
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

    The separator can be expanded automatically with the ``--fix`` option.

    """

    name = "not-enough-whitespace-after-suite-setting"
    rule_id = "SPC22"
    message = "Not enough whitespace after '{setting_name}' setting"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("0411",)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        return expand_separator_fix(self, diag, source_lines)
