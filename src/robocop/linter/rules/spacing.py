"""Spacing checkers"""

from __future__ import annotations

import re
from collections import Counter
from itertools import takewhile
from typing import TYPE_CHECKING, ClassVar

from robot.api import Token
from robot.parsing.model.blocks import TestCase
from robot.parsing.model.statements import Comment, EmptyLine, TemplateArguments

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit, remove_lines_fix
from robocop.linter.rules import (
    FixableRule,
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
)
from robocop.linter.utils.misc import str2bool

if TYPE_CHECKING:
    from robot.parsing.model import Section
    from robot.parsing.model.statements import Arguments, Node, Statement

    from robocop.linter.diagnostics import Diagnostic


class TrailingWhitespaceRule(FixableRule):
    r"""
    Trailing whitespace at the end of the line.

    Invisible, unnecessary whitespace can be confusing.

    Incorrect code example:

        *** Keywords ***  \n
        Validate Result\n
        [Arguments]    ${variable}\n
            Should Be True    ${variable}    \n

    Correct code:

        *** Keywords ***\n
        Validate Result\n
        [Arguments]    ${variable}\n
            Should Be True    ${variable}\n

    """

    name = "trailing-whitespace"
    rule_id = "SPC01"
    message = "Trailing whitespace at the end of line"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    style_guide_ref = ["#trailing-whitespaces"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1001",)
    fix_availability = FixAvailability.ALWAYS

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        return Fix(
            edits=[TextEdit.replace_at_range(self.rule_id, self.name, diag.range, "")],
            message="Strip trailing whitespace",
            applicability=FixApplicability.SAFE,
        )

    def check(self, line: str, lineno: int) -> None:
        if not self.enabled:
            return
        stripped_line = line.rstrip("\n\r")
        if not stripped_line or stripped_line[-1] not in " \t":
            return
        whitespace_length = len(stripped_line) - len(stripped_line.rstrip())
        self.report(
            lineno=lineno,
            col=len(stripped_line) - whitespace_length + 1,
            end_col=len(stripped_line) + 1,
        )


class MissingTrailingBlankLineRule(Rule):
    """
    Missing trailing blank line at the end of file.

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "missing-trailing-blank-line"
    rule_id = "SPC02"
    message = "Missing trailing blank line at the end of file"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    style_guide_ref = ["#spacing-after-sections"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1002",)

    def check(self, lines: list[str]) -> None:
        if not self.enabled or not lines:
            return
        last_line = lines[-1]
        # blank last line is handled by too-many-trailing-blank-lines
        if last_line.strip() and not last_line.endswith(("\n", "\r")):
            self.report(lineno=len(lines), end_col=len(last_line) + 1)


class EmptyLinesBetweenSectionsRule(Rule):
    """
    Invalid number of empty lines between sections.

    Ensure there is the same number of empty lines between sections for consistency and readability.

    Incorrect code example:

        *** Settings ***
        Documentation    Only one empty line after this section.

        *** Keywords ***
        Keyword Definition
            No Operation

    Correct code:

        *** Settings ***
        Documentation    Only one empty line after this section.


        *** Keywords ***
        Keyword Definition
            No Operation

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-lines-between-sections"
    rule_id = "SPC03"
    message = "Invalid number of empty lines between sections ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="empty_lines",
            default=2,
            converter=int,
            desc="number of empty lines required between sections",
        )
    ]
    added_in_version = "1.0.0"
    style_guide_ref = ["#spacing-after-sections"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1003",)


class EmptyLinesBetweenTestCasesRule(Rule):
    """
    Invalid number of empty lines between test cases.

    Ensure there is the same number of empty lines between test cases for consistency and readability.

    Incorrect code example:

        *** Test Cases ***
        First test case
            No Operation


        Second test case
            No Operation

    Correct code:

        *** Test Cases ***
        First test case
            No Operation

        Second test case
            No Operation

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-lines-between-test-cases"
    rule_id = "SPC04"
    message = "Invalid number of empty lines between test cases ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between test cases",
        )
    ]
    added_in_version = "1.0.0"
    style_guide_ref = ["#spacing-after-test-cases-or-tasks"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1004",)


class EmptyLinesBetweenKeywordsRule(Rule):
    """
    Invalid number of empty lines between keywords.

    Ensure there is the same number of empty lines between keywords for consistency and readability.

    Incorrect code example:

        *** Keywords ***
        First Keyword
            No Operation


        Second Keyword
            No Operation

    Correct code:

        *** Keywords ***
        First Keyword
            No Operation

        Second Keyword
            No Operation

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-lines-between-keywords"
    rule_id = "SPC05"
    message = "Invalid number of empty lines between keywords ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between keywords",
        )
    ]
    added_in_version = "1.0.0"
    style_guide_ref = ["#spacing-after-keywords"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1005",)


class MixedTabsAndSpacesRule(Rule):
    """
    Mixed tabs and spaces in the file.

    File contains both spaces and tabs. Use only one type of separators - preferably spaces.

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
    (``robocop format``) to fix it.

    """

    name = "mixed-tabs-and-spaces"
    rule_id = "SPC06"
    message = "Inconsistent use of tabs and spaces in file"
    severity = RuleSeverity.WARNING
    added_in_version = "1.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1006",)


class BadIndentRule(Rule):
    """
    Line is misaligned or indent is invalid.

    This rule reports a warning if the line is misaligned in the current block.
    The correct indentation is determined by the most common indentation in the current block.
    It is possible to switch for stricter mode using the `` indent `` parameter (default ``-1``).

    Incorrect code example:

        *** Keywords ***
        Keyword
            Keyword Call
             Misaligned Keyword Call
            IF    $condition    RETURN
           Keyword Call

    Correct code:

        *** Keywords ***
        Keyword
            Keyword Call
            Misaligned Keyword Call
            IF    $condition    RETURN
            Keyword Call

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
    (``robocop format``) to fix it.

    """

    name = "bad-indent"
    rule_id = "SPC08"
    message = "{bad_indent_msg}"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="indent",
            default=-1,
            converter=int,
            desc="Number of spaces per indentation level",
        )
    ]
    added_in_version = "3.0.0"
    style_guide_ref = [
        "#indentation",
        "#block-indentation",
        "#indentation-within-test-cases-tasks-and-keywords-section",
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1008",)


class EmptyLineAfterSectionRule(Rule):
    """
    Too many empty lines after the section header.

    Empty lines after the section header are not allowed by default.

    Incorrect code example:

         *** Test Cases ***

         Test case name

    Correct code:

         *** Test Cases ***
         Test case name

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-line-after-section"
    rule_id = "SPC09"
    message = "Too many empty lines after '{section_name}' section header ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="empty_lines",
            default=0,
            converter=int,
            desc="number of empty lines allowed after section header",
        )
    ]
    severity_threshold = SeverityThreshold("empty_lines", substitute_value="allowed_empty_lines")
    added_in_version = "1.2.0"
    style_guide_ref = ["#spacing-after-the-section-header-line"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1009",)


class TooManyTrailingBlankLinesRule(Rule):
    """
    Too many blank lines at the end of the file.

    There should be exactly one blank line at the end of the file.

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "too-many-trailing-blank-lines"
    rule_id = "SPC10"
    message = "Too many blank lines at the end of file"
    file_wide_rule = True  # TODO: improve checking to report on trailing lines
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    style_guide_ref = ["#spacing-after-sections"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1010",)

    def check(self, lines: list[str]) -> None:
        if not self.enabled or not lines:
            return
        last_line = lines[-1]
        if last_line in ("\n", "\r", "\r\n"):
            self.report(lineno=len(lines) + 1, end_col=len(last_line) + 1)
            return
        trailing_empty_lines = takewhile(lambda line: not line.strip(), reversed(lines))
        if sum(1 for _ in trailing_empty_lines) > 1:
            self.report(lineno=len(lines), end_col=len(last_line) + 1)


class MisalignedContinuationRule(Rule):
    """
    Misaligned continuation marker.

    Incorrect code example:

        *** Settings ***
            Default Tags       default tag 1    default tag 2    default tag 3
        ...                default tag 4    default tag 5

        *** Test Cases ***
        Example
            Do X    first argument    second argument    third argument
          ...    fourth argument    fifth argument    sixth argument

    Correct code:

        *** Settings ***
        Default Tags       default tag 1    default tag 2    default tag 3
        ...                default tag 4    default tag 5

        *** Test Cases ***
        Example
            Do X    first argument    second argument    third argument
            ...    fourth argument    fifth argument    sixth argument

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
    (``robocop format``) to fix it.

    """

    name = "misaligned-continuation"
    rule_id = "SPC11"
    message = "Continuation marker is not aligned with starting row"
    severity = RuleSeverity.WARNING
    added_in_version = "1.6.0"
    style_guide_ref = ["#variables-section-line-continuation"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1011",)


class ConsecutiveEmptyLinesRule(Rule):
    """
    Too many consecutive empty lines.

    Incorrect code example:

        *** Variables ***
        ${VAR}    value


        ${VAR2}    value


        *** Keywords ***
        Keyword
            Step 1


            Step 2

    Correct code:

        *** Variables ***
        ${VAR}    value
        ${VAR2}    value


        *** Keywords ***
        Keyword
            Step 1
            Step 2  # 1 empty line is also fine, but no more

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "consecutive-empty-lines"
    rule_id = "SPC12"
    message = "Too many consecutive empty lines ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of allowed consecutive empty lines",
        )
    ]
    severity_threshold = SeverityThreshold(
        "empty_lines", compare_method="greater", substitute_value="allowed_empty_lines"
    )
    added_in_version = "1.8.0"
    style_guide_ref = [
        "#settings-1",
        "#spacing-between-code-blocks-within-test-cases-or-tasks",
        "#spacing-between-code-blocks-within-keyword-calls",
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1012",)


class EmptyLinesInStatementRule(Rule):
    """
    Multi-line statement with empty lines.

    Avoid using empty lines between continuation markers in multi line statement.

    Incorrect code example:

        *** Test Cases ***
        Test case
            Keyword
            ...  1
            # empty line in-between multiline statement
            ...  2

            ...  3

    Correct code:

        *** Test Cases ***
        Test case
            Keyword
            ...  1
            ...  2
            ...  3

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-lines-in-statement"
    rule_id = "SPC13"
    message = "Multi-line statement with empty lines"
    severity = RuleSeverity.WARNING
    added_in_version = "1.8.0"
    style_guide_ref = ["#spacing-of-line-continuations"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1013",)


class VariableNotLeftAlignedRule(Rule):
    """
    Variable in ``*** Variables ***`` section should be left aligned.

    Incorrect code example:

        *** Variables ***
         ${VAR}  1
          ${VAR2}  2

    Correct code:

        *** Variables ***
        ${VAR}  1
        ${VAR2}  2

    This rule is not fixed by ``robocop check --fix``. Use the ``AlignVariablesSection`` formatter
    (``robocop format``) to fix it.

    """

    name = "variable-not-left-aligned"
    rule_id = "SPC14"
    message = "Variable in Variables section is not left aligned"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.8.0"
    style_guide_ref = ["#indentation-within-variables-section"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1014", "variable-should-be-left-aligned")

    def check(self, node: Section) -> None:
        if not self.enabled:
            return
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and (token.value == "" or token.value.startswith(" ")):
                if token.value or not child.get_token(Token.ARGUMENT):
                    pos = len(token.value) - len(token.value.lstrip()) + 1
                else:
                    pos = child.get_token(Token.ARGUMENT).col_offset + 1
                self.report(lineno=token.lineno, col=1, end_col=pos)


class MisalignedContinuationRowRule(Rule):
    """
    The continuation marker should be aligned with the previous one.

    Incorrect code example:

        *** Variable ***
        ${VAR}    This is a long string.
        ...       It has multiple sentences.
        ...         And this line is misaligned with previous one.

        *** Test Cases ***
        My Test
            My Keyword
            ...    arg1
            ...   arg2  # misaligned

    Correct code:

        *** Variable ***
        ${VAR}    This is a long string.
        ...       It has multiple sentences.
        ...       And this line is misaligned with previous one.

        *** Test Cases ***
        My Test
            My Keyword
            ...    arg1
            ...    arg2  # misaligned

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
    (``robocop format``) to fix it.

    """

    name = "misaligned-continuation-row"
    rule_id = "SPC15"
    message = "Continuation line is not aligned with the previous one"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(name="ignore_docs", default=True, converter=str2bool, show_type="bool", desc="Ignore documentation"),
        RuleParam(
            name="ignore_run_keywords", default=False, converter=str2bool, show_type="bool", desc="Ignore run keywords"
        ),
    ]
    added_in_version = "1.11.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1015",)


class SuiteSettingNotLeftAlignedRule(Rule):
    """
    Settings in the ``*** Settings ***`` section should be left aligned.

    Incorrect code example:

        *** Settings ***
            Library  Collections
        Resource  data.resource
            Variables  vars.robot

    Correct code:

        *** Settings ***
        Library  Collections
        Resource  data.resource
        Variables  vars.robot

    """

    name = "suite-setting-not-left-aligned"
    rule_id = "SPC16"
    message = "Setting in Settings section is not left aligned"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "2.4.0"
    style_guide_ref = ["#indentation-within-settings-section"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )
    deprecated_names = ("1016", "suite-setting-should-be-left-aligned")

    suite_settings: ClassVar[dict[str, str]] = {
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
    non_existing_setting_pattern = re.compile("Non-existing setting '(.*)'.")

    def check(self, node: Section) -> None:
        if not self.enabled:
            return
        for child in node.body:
            for error in child.errors:
                if "Non-existing setting" in error:
                    self.parse_error(child, error)

    def parse_error(self, node: Statement, error: str) -> None:
        error_match = self.non_existing_setting_pattern.search(error)
        if not error_match:
            return
        setting_error = error_match.group(1)
        if not setting_error:
            setting_cand = node.get_token(Token.COMMENT)
            if setting_cand and setting_cand.value.replace(" ", "").lower() in self.suite_settings:
                self.report(
                    node=setting_cand,
                    col=setting_cand.col_offset + 1,
                    end_col=setting_cand.end_col_offset + 1,
                )
        elif not setting_error[0].strip():  # starts with space/tab
            suite_sett_cand = setting_error.replace(" ", "").lower()
            for setting in self.suite_settings:
                if suite_sett_cand.startswith(setting):
                    indent = len(setting_error) - len(setting_error.lstrip())
                    self.report(node=node, col=indent + 1)
                    break


class BadBlockIndentRule(Rule):
    """
    Not enough indentation.

    Reports occurrences where indentation is less than two spaces than current block parent element (such as
    ``FOR``/``IF``/``WHILE``/``TRY`` header).

    Incorrect code example:

        *** Keywords ***
        Some Keyword
            FOR  ${elem}  IN  ${list}
                Log  ${elem}  # this is fine
           Log  stuff    # this is bad indent
        # bad comment
            END

    Correct code:

        *** Keywords ***
        Some Keyword
            FOR  ${elem}  IN  ${list}
                Log  ${elem}  # this is fine
                Log  stuff    # this is bad indent
                # bad comment
            END

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeSeparators`` formatter
    (``robocop format``) to fix it.

    """

    name = "bad-block-indent"
    rule_id = "SPC17"
    message = "Not enough indentation inside block"
    severity = RuleSeverity.ERROR
    added_in_version = "3.0.0"
    style_guide_ref = ["#indentation"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1017",)


class FirstArgumentInNewLineRule(Rule):
    """
    The first argument is not in the same level as the ``[Arguments]`` setting.

    Incorrect code example:

        *** Keywords ***
        Custom Keyword With Five Required Arguments
        [Arguments]
        ...    ${name}
        ...    ${surname}

    Correct code:

        *** Keywords ***
        Custom Keyword With Five Required Arguments
        [Arguments]    ${name}
        ...    ${surname}

    """

    name = "first-argument-in-new-line"
    rule_id = "SPC18"
    message = "First argument: '{argument_name}' is not placed on the same line as [Arguments] setting"
    severity = RuleSeverity.WARNING
    added_in_version = "5.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("1018",)

    def check(self, node: Arguments) -> None:
        if not self.enabled:
            return
        eol_already = None
        for token in node.tokens:
            if token.type == Token.EOL:
                eol_already = token
            elif token.type == Token.ARGUMENT:
                if eol_already is not None:
                    self.report(
                        argument_name=token.value,
                        lineno=eol_already.lineno,
                        end_lineno=token.lineno,
                        col=eol_already.end_col_offset,
                        end_col=token.end_col_offset,
                    )
                return


class EmptyLineInTestTemplateRule(FixableRule):
    """
    Empty line in test template data.

    Robot Framework ignores empty lines between data rows in templated tests. Remove these lines so that the test data
    does not contain rows that have no effect.

    Incorrect code example:

        *** Test Cases ***
        Example
            [Template]    Template Keyword
            first argument

            second argument

    Correct code:

        *** Test Cases ***
        Example
            [Template]    Template Keyword
            first argument
            second argument

    The rule reports only empty lines between consecutive template data rows, including rows nested in control
    structures. Blank lines next to settings or comments and blank lines separating test cases are preserved.

    The fix removes the ignored empty line.
    """

    name = "empty-line-in-test-template"
    rule_id = "SPC23"
    message = "Empty line in test template data"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "9.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )

    def check(self, node: TestCase) -> None:
        if not self.enabled:
            return
        self.check_body(node.body)

    def check_body(self, body: list[Node]) -> None:
        empty_lines: list[EmptyLine] = []
        template_data_row_seen = False
        for statement in body:
            if isinstance(statement, TemplateArguments):
                if template_data_row_seen:
                    for empty_line in empty_lines:
                        self.report(node=empty_line, col=1)
                template_data_row_seen = True
                empty_lines = []
            elif isinstance(statement, EmptyLine) and template_data_row_seen:
                empty_lines.append(statement)
            else:
                template_data_row_seen = False
                empty_lines = []
            nested_body = getattr(statement, "body", None)
            if nested_body is not None:
                self.check_body(nested_body)
            for branch_attr in ("orelse", "next"):
                branch = getattr(statement, branch_attr, None)
                while branch is not None:
                    self.check_body(branch.body)
                    branch = getattr(branch, branch_attr, None)

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        if diag.node is None:
            return None
        return remove_lines_fix(
            self,
            start_line=diag.node.lineno,
            end_line=diag.node.end_lineno,
            message="Remove the ignored empty line",
        )


class EmptyLinesInsideBlockRule(Rule):
    """
    Empty lines after a block header or before the block end.

    Empty lines directly after a block header (``FOR``, ``WHILE``, ``IF``/``ELSE``, ``TRY``/``EXCEPT`` or ``GROUP``)
    or directly before the block end are not allowed by default.

    Incorrect code example:

        *** Keywords ***
        Iterate
            FOR    ${var}    IN    1    2

                Keyword Call

            END

    Correct code:

        *** Keywords ***
        Iterate
            FOR    ${var}    IN    1    2
                Keyword Call
            END

    The number of allowed empty lines can be configured using the ``empty_lines`` parameter::

        robocop check --configure empty-lines-inside-block.empty_lines=1

    This rule is not fixed by ``robocop check --fix``. Use the ``NormalizeNewLines`` formatter
    (``robocop format``) to fix it.

    """

    name = "empty-lines-inside-block"
    rule_id = "SPC24"
    message = "Empty lines {block_position} ({empty_lines}/{allowed_empty_lines})"
    severity = RuleSeverity.INFO
    parameters = [
        RuleParam(
            name="empty_lines",
            default=0,
            converter=int,
            desc="number of allowed empty lines after a block header or before the block end",
        )
    ]
    severity_threshold = SeverityThreshold(
        "empty_lines", compare_method="greater", substitute_value="allowed_empty_lines"
    )
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )


def get_indent(node: Node) -> int:
    """
    Calculate the indentation length for a given node.

    Returns:
        int: Indentation length

    """
    tokens = node.tokens if hasattr(node, "tokens") else node.header.tokens
    indent_len = 0
    for token in tokens:
        if token.type != Token.SEPARATOR:
            break
        indent_len += len(token.value.expandtabs(4))
    return indent_len


def count_indents(node: Node) -> Counter[int]:
    """
    Count the number of occurrences for unique indent values

    Returns:
        Counter: A counter of unique indent values with an associated number of occurrences in the given node

    """
    indents: Counter[int] = Counter()
    if node is None:
        return indents
    for line in node.body:
        if isinstance(line, (EmptyLine, Comment)):
            continue
        # for templated suite, there can be data on the same line where the test case name is
        if node.lineno == line.lineno and isinstance(node, TestCase):
            indents[len(node.name) + (get_indent(line))] += 1
        else:
            indents[(get_indent(line))] += 1
    return indents


def most_common_indent(indents: Counter[int]) -> int:
    """
    Return most commonly occurred indent

    Args:
        indents (Counter): A counter of unique indent values with associated number of occurrences in given node

    Returns:
        indent (int): Most common indent or the first one

    """
    common_indents = indents.most_common(1)
    if not common_indents:
        return 0
    indent, _ = common_indents[0]
    return indent


def index_of_first_standalone_comment(node: Node) -> int:
    """
    Get index of first standalone comment.
    Comment can be standalone only if there are not the other data statements in the node.
    """
    last_standalone_comment = len(node.body)
    for index, child in enumerate(node.body[::-1], start=-(len(node.body) - 1)):
        if not isinstance(child, (EmptyLine, Comment)):
            return last_standalone_comment
        if isinstance(child, Comment) and get_indent(child) == 0:
            last_standalone_comment = abs(index)
    return last_standalone_comment
