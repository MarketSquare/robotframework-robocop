"""Spacing checkers"""

from __future__ import annotations

import re
from collections import Counter
from contextlib import contextmanager
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import Keyword, TestCase
from robot.parsing.model.statements import Comment, EmptyLine, KeywordCall
from robot.parsing.model.visitor import ModelVisitor

from robocop.linter.utils.misc import ROBOT_VERSION

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

from robocop.linter.rules import RawFileChecker, Rule, RuleParam, RuleSeverity, SeverityThreshold, VisitorChecker
from robocop.linter.utils import get_errors, get_section_name, str2bool, token_col
from robocop.linter.utils.run_keywords import is_run_keyword

if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model import Block, Section
    from robot.parsing.model.statements import Node, Statement

    from robocop.linter.rules import BaseChecker


class TrailingWhitespaceRule(Rule):
    r"""
    Trailing whitespace at the end of line.

    Invisible, unnecessary whitespace can be confusing.

    Incorrect code example::

        *** Keywords ***  \n
        Validate Result\n
        [Arguments]    ${variable}\n
            Should Be True    ${variable}    \n

    Correct code::

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


class MissingTrailingBlankLineRule(Rule):
    """Missing trailing blank line at the end of file."""

    name = "missing-trailing-blank-line"
    rule_id = "SPC02"
    message = "Missing trailing blank line at the end of file"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    style_guide_ref = ["#spacing-after-sections"]


class EmptyLinesBetweenSectionsRule(Rule):
    """
    Invalid number of empty lines between sections.

    Ensure there is the same number of empty lines between sections for consistency and readability.

    Incorrect code example::

        *** Settings ***
        Documentation    Only one empty line after this section.

        *** Keywords ***
        Keyword Definition
            No Operation

    Correct code::

        *** Settings ***
        Documentation    Only one empty line after this section.


        *** Keywords ***
        Keyword Definition
            No Operation

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


class EmptyLinesBetweenTestCasesRule(Rule):
    """
    Invalid number of empty lines between test cases.

    Ensure there is the same number of empty lines between test cases for consistency and readability.

    Incorrect code example::

        *** Test Cases ***
        First test case
            No Operation


        Second test case
            No Operation

    Correct code::

        *** Test Cases ***
        First test case
            No Operation

        Second test case
            No Operation

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


class EmptyLinesBetweenKeywordsRule(Rule):
    """
    Invalid number of empty lines between keywords.

    Ensure there is the same number of empty lines between keywords for consistency and readability.

    Incorrect code example::

        *** Keywords ***
        First Keyword
            No Operation


        Second Keyword
            No Operation

    Correct code::

        *** Keywords ***
        First Keyword
            No Operation

        Second Keyword
            No Operation

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


class MixedTabsAndSpacesRule(Rule):
    """
    Mixed tabs and spaces in file.

    File contains both spaces and tabs. Use only one type of separators - preferably spaces.
    """

    name = "mixed-tabs-and-spaces"
    rule_id = "SPC06"
    message = "Inconsistent use of tabs and spaces in file"
    file_wide_rule = True
    severity = RuleSeverity.WARNING
    added_in_version = "1.1.0"


class BadIndentRule(Rule):
    """
    Line is misaligned or indent is invalid.

    This rule reports warning if the line is misaligned in the current block.
    The correct indentation is determined by the most common indentation in the current block.
    It is possible to switch for more strict mode using ``indent`` parameter (default ``-1``).

    Incorrect code example::

        *** Keywords ***
        Keyword
            Keyword Call
             Misaligned Keyword Call
            IF    $condition    RETURN
           Keyword Call

    Correct code::

        *** Keywords ***
        Keyword
            Keyword Call
            Misaligned Keyword Call
            IF    $condition    RETURN
            Keyword Call

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


class EmptyLineAfterSectionRule(Rule):
    """
    Too many empty lines after section header.

    Empty lines after the section header are not allowed by default.

    Incorrect code example::

         *** Test Cases ***

         Test case name

    Correct code::

         *** Test Cases ***
         Test case name

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


class TooManyTrailingBlankLinesRule(Rule):
    """
    Too many blank lines at the end of file.

    There should be exactly one blank line at the end of the file.
    """

    name = "too-many-trailing-blank-lines"
    rule_id = "SPC10"
    message = "Too many blank lines at the end of file"
    file_wide_rule = True  # TODO: improve checking to report on trailing lines
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    style_guide_ref = ["#spacing-after-sections"]


class MisalignedContinuationRule(Rule):
    """
    Misaligned continuation marker.

    Incorrect code example::

        *** Settings ***
            Default Tags       default tag 1    default tag 2    default tag 3
        ...                default tag 4    default tag 5

        *** Test Cases ***
        Example
            Do X    first argument    second argument    third argument
          ...    fourth argument    fifth argument    sixth argument

    Correct code::

        *** Settings ***
        Default Tags       default tag 1    default tag 2    default tag 3
        ...                default tag 4    default tag 5

        *** Test Cases ***
        Example
            Do X    first argument    second argument    third argument
            ...    fourth argument    fifth argument    sixth argument

    """

    name = "misaligned-continuation"
    rule_id = "SPC11"
    message = "Continuation marker is not aligned with starting row"
    severity = RuleSeverity.WARNING
    added_in_version = "1.6.0"
    style_guide_ref = ["#variables-section-line-continuation"]


class ConsecutiveEmptyLinesRule(Rule):
    """
    Too many consecutive empty lines.

    Incorrect code example::

        *** Variables ***
        ${VAR}    value


        ${VAR2}    value


        *** Keywords ***
        Keyword
            Step 1


            Step 2

    Correct code::

        *** Variables ***
        ${VAR}    value
        ${VAR2}    value


        *** Keywords ***
        Keyword
            Step 1
            Step 2  # 1 empty line is also fine, but no more

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


class EmptyLinesInStatementRule(Rule):
    """
    Multi line statement with empty lines.

    Avoid using empty lines between continuation markers in multi line statement.

    Incorrect code example::

        *** Test Cases ***
        Test case
            Keyword
            ...  1
            # empty line in-between multiline statement
            ...  2

            ...  3

    Correct code::

        *** Test Cases ***
        Test case
            Keyword
            ...  1
            ...  2
            ...  3

    """

    name = "empty-lines-in-statement"
    rule_id = "SPC13"
    message = "Multi-line statement with empty lines"
    severity = RuleSeverity.WARNING
    added_in_version = "1.8.0"
    style_guide_ref = ["#spacing-of-line-continuations"]


class VariableNotLeftAlignedRule(Rule):
    """
    Variable in ``*** Variables ***`` section should be left aligned.

    Incorrect code example::

        *** Variables ***
         ${VAR}  1
          ${VAR2}  2

    Correct code::

        *** Variables ***
        ${VAR}  1
        ${VAR2}  2

    """

    name = "variable-not-left-aligned"
    rule_id = "SPC14"
    message = "Variable in Variables section is not left aligned"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.8.0"
    style_guide_ref = ["#indentation-within-variables-section"]


class MisalignedContinuationRowRule(Rule):
    """
    Continuation marker should be aligned with the previous one.

    Incorrect code example::

        *** Variable ***
        ${VAR}    This is a long string.
        ...       It has multiple sentences.
        ...         And this line is misaligned with previous one.

        *** Test Cases ***
        My Test
            My Keyword
            ...    arg1
            ...   arg2  # misaligned

    Correct code::

        *** Variable ***
        ${VAR}    This is a long string.
        ...       It has multiple sentences.
        ...       And this line is misaligned with previous one.

        *** Test Cases ***
        My Test
            My Keyword
            ...    arg1
            ...    arg2  # misaligned

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


class SuiteSettingNotLeftAlignedRule(Rule):
    """
    Settings in ``*** Settings ***`` section should be left aligned.

    Incorrect code example::

        *** Settings ***
            Library  Collections
        Resource  data.resource
            Variables  vars.robot

    Correct code::

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


class BadBlockIndentRule(Rule):
    """
    Not enough indentation.

    Reports occurrences where indentation is less than two spaces than current block parent element (such as
    ``FOR``/``IF``/``WHILE``/``TRY`` header).

    Incorrect code example::

        *** Keywords ***
        Some Keyword
            FOR  ${elem}  IN  ${list}
                Log  ${elem}  # this is fine
           Log  stuff    # this is bad indent
        # bad comment
            END

    Correct code::

        *** Keywords ***
        Some Keyword
            FOR  ${elem}  IN  ${list}
                Log  ${elem}  # this is fine
                Log  stuff    # this is bad indent
                # bad comment
            END

    """

    name = "bad-block-indent"
    rule_id = "SPC17"
    message = "Not enough indentation inside block"
    severity = RuleSeverity.ERROR
    added_in_version = "3.0.0"
    style_guide_ref = ["#indentation"]


class FirstArgumentInNewLineRule(Rule):
    """
    First argument is not in the same level as ``[Arguments]`` setting.

    Incorrect code example::

        *** Keywords ***
        Custom Keyword With Five Required Arguments
        [Arguments]
        ...    ${name}
        ...    ${surname}

    Correct code::

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


class InvalidSpacingChecker(RawFileChecker):  # TODO merge, we can just use single RawFileChecker
    """Checker for trailing spaces and lines."""

    trailing_whitespace: TrailingWhitespaceRule
    missing_trailing_blank_line: MissingTrailingBlankLineRule
    too_many_trailing_blank_lines: TooManyTrailingBlankLinesRule

    def __init__(self):
        self.raw_lines = []
        super().__init__()

    def parse_file(self) -> None:
        self.raw_lines = []
        super().parse_file()
        if self.raw_lines:
            last_line = self.raw_lines[-1]
            if last_line in ["\n", "\r", "\r\n"]:
                self.report(
                    self.too_many_trailing_blank_lines, lineno=len(self.raw_lines) + 1, end_col=len(last_line) + 1
                )
                return
            empty_lines = 0
            for line in self.raw_lines[::-1]:
                if not line.strip():
                    empty_lines += 1
                else:
                    break
                if empty_lines > 1:
                    self.report(
                        self.too_many_trailing_blank_lines, lineno=len(self.raw_lines), end_col=len(last_line) + 1
                    )
                    return
            if not empty_lines and not last_line.endswith(("\n", "\r")):
                self.report(self.missing_trailing_blank_line, lineno=len(self.raw_lines), end_col=len(last_line) + 1)

    def check_line(self, line: str, lineno: int) -> None:
        self.raw_lines.append(line)

        stripped_line = line.rstrip("\n\r")
        if stripped_line and stripped_line[-1] in [" ", "\t"]:
            whitespace_length = len(stripped_line) - len(stripped_line.rstrip())
            self.report(
                self.trailing_whitespace,
                lineno=lineno,
                col=len(stripped_line) - whitespace_length + 1,
                end_col=len(stripped_line) + 1,
            )


class EmptyLinesChecker(VisitorChecker):
    """Checker for invalid spacing."""

    empty_lines_between_sections: EmptyLinesBetweenSectionsRule
    empty_lines_between_test_cases: EmptyLinesBetweenTestCasesRule
    empty_lines_between_keywords: EmptyLinesBetweenKeywordsRule
    empty_line_after_section: EmptyLineAfterSectionRule
    consecutive_empty_lines: ConsecutiveEmptyLinesRule
    empty_lines_in_statement: EmptyLinesInStatementRule

    def verify_consecutive_empty_lines(
        self, lines: list[Statement], check_leading: bool = True, check_trailing: bool = False
    ):
        allowed_consecutive = self.consecutive_empty_lines.empty_lines
        empty_lines = 0
        last_empty_line = None
        data_found = check_leading
        for line in lines:
            if isinstance(line, EmptyLine):
                if not data_found:
                    continue
                empty_lines += 1
                last_empty_line = line
            else:
                data_found = True
                # allow for violation at the end of section, because we have 1003 rule
                if empty_lines > allowed_consecutive:  # and i != len(lines)-1:
                    self.report(
                        self.consecutive_empty_lines,
                        empty_lines=empty_lines,
                        allowed_empty_lines=allowed_consecutive,
                        node=last_empty_line,
                        sev_threshold_value=empty_lines,
                        col=1,
                        lineno=last_empty_line.lineno - empty_lines + 1,
                        end_lineno=last_empty_line.lineno,
                    )
                empty_lines = 0
        if check_trailing and empty_lines > allowed_consecutive:
            self.report(
                self.consecutive_empty_lines,
                empty_lines=empty_lines,
                allowed_empty_lines=allowed_consecutive,
                node=last_empty_line,
                sev_threshold_value=empty_lines,
                col=1,
                lineno=last_empty_line.lineno - empty_lines + 1,
                end_lineno=last_empty_line.lineno,
            )
        return empty_lines

    def check_empty_lines_in_keyword_test(self, node: type[Node]):
        """
        Verify number of consecutive empty lines inside keyword or test.
        Return number of trailing empty lines.
        """
        # split node and trailing empty lines/comments
        end_found = False
        node_lines, trailing_lines = [], []
        for child in node.body[::-1]:
            if not end_found and isinstance(child, (EmptyLine, Comment)):
                trailing_lines.append(child)
            else:
                end_found = True
                node_lines.append(child)
        self.verify_consecutive_empty_lines(reversed(node_lines))
        return self.verify_consecutive_empty_lines(reversed(trailing_lines))

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        prev_token = None
        for token in node.tokens:
            if token.type == Token.EOL:
                if prev_token:
                    self.report(self.empty_lines_in_statement, node=token)
                prev_token = token
            else:
                prev_token = None

    def visit_VariableSection(self, node: type[Node]) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def visit_SettingSection(self, node: type[Node]) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def verify_empty_lines_between_nodes(
        self, node: type[Node], node_type: type, rule: Rule, allowed_empty_lines: int
    ) -> None:
        last_index = len(node.body) - 1
        for index, child in enumerate(node.body):
            if not isinstance(child, node_type):
                continue
            empty_lines = self.check_empty_lines_in_keyword_test(child)
            if allowed_empty_lines not in (empty_lines, -1) and index < last_index:
                lineno = min(child.end_lineno - empty_lines + 1, child.end_lineno)
                self.report(
                    rule,
                    empty_lines=empty_lines,
                    allowed_empty_lines=allowed_empty_lines,
                    lineno=lineno,
                    end_lineno=child.end_lineno,
                )
        self.generic_visit(node)

    def visit_TestCaseSection(self, node: type[Node]) -> None:  # noqa: N802
        allowed_lines = -1 if self.templated_suite else self.empty_lines_between_test_cases.empty_lines
        self.verify_empty_lines_between_nodes(node, TestCase, self.empty_lines_between_test_cases, allowed_lines)

    def visit_KeywordSection(self, node: type[Node]) -> None:  # noqa: N802
        self.verify_empty_lines_between_nodes(
            node,
            Keyword,
            self.empty_lines_between_keywords,
            self.empty_lines_between_keywords.empty_lines,
        )

    def visit_For(self, node: type[Node]) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_trailing=True)
        self.generic_visit(node)

    visit_ForLoop = visit_While = visit_Try = visit_If = visit_Group = visit_For  # noqa: N815

    def visit_File(self, node: File) -> None:  # noqa: N802
        for section in node.sections:
            self.check_empty_lines_after_section(section)
        for section in node.sections[:-1]:
            if not section.header:  # for comment section
                continue
            empty_lines = 0
            child = section  # workaround for empty sections when reporting issue
            for child in reversed(section.body):
                if isinstance(child, (Keyword, TestCase)):
                    for statement in reversed(child.body):
                        if isinstance(statement, EmptyLine):
                            empty_lines += 1
                        else:
                            break
                if isinstance(child, EmptyLine):
                    empty_lines += 1
                else:
                    break
            if empty_lines != self.empty_lines_between_sections.empty_lines:
                self.report(
                    self.empty_lines_between_sections,
                    empty_lines=empty_lines,
                    allowed_empty_lines=self.empty_lines_between_sections.empty_lines,
                    lineno=section.end_lineno,
                    col=1,
                    end_col=child.end_col_offset,
                )
        super().visit_File(node)

    def check_empty_lines_after_section(self, section: Section) -> None:
        empty_lines = []
        for child in section.body:
            if not isinstance(child, EmptyLine):
                break
            empty_lines.append(child)
        else:
            return
        if len(empty_lines) > self.empty_line_after_section.empty_lines:
            self.report(
                self.empty_line_after_section,
                section_name=get_section_name(section),
                empty_lines=len(empty_lines),
                allowed_empty_lines=self.empty_line_after_section.empty_lines,
                node=empty_lines[-1],
                sev_threshold_value=len(empty_lines),
                lineno=section.lineno,
                end_col=len(get_section_name(section)) + 1,
            )


class InconsistentUseOfTabsAndSpacesChecker(VisitorChecker):  # TODO: add found tab in file rule (to list them all)
    """Checker for inconsistent use of tabs and spaces."""

    mixed_tabs_and_spaces: MixedTabsAndSpacesRule

    def __init__(self):
        self.found, self.tabs, self.spaces = False, False, False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.found, self.tabs, self.spaces = False, False, False
        super().visit_File(node)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        if self.found:
            return
        for token in node.get_tokens(Token.SEPARATOR):
            self.tabs = "\t" in token.value or self.tabs
            self.spaces = " " in token.value or self.spaces

            if self.tabs and self.spaces:
                self.report(self.mixed_tabs_and_spaces, node=node, lineno=1)
                self.found = True
                break


def get_indent(node: type[Node]) -> int:
    """
    Calculate the indentation length for given node

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


def count_indents(node: type[Node]) -> Counter:
    """
    Count number of occurrences for unique indent values

    Returns:
        Counter: A counter of unique indent values with associated number of occurrences in given node

    """
    indents = Counter()
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


def most_common_indent(indents: Counter) -> int:
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


@contextmanager
def replace_parent_indent(checker: type[BaseChecker], node: type[Node]):
    """Temporarily replace parent indent with current node indent."""
    parent_line = checker.parent_line
    parent_indent = checker.parent_indent
    checker.parent_indent = get_indent(node)
    checker.parent_line = node.lineno
    yield
    checker.parent_indent = parent_indent
    checker.parent_line = parent_line


@contextmanager
def block_indent(checker: type[BaseChecker], node: type[Node]):
    """
    Temporarily replace parent indent and store
    current node indents in the stack.
    """
    with replace_parent_indent(checker, node):
        indents = count_indents(node)
        most_common = most_common_indent(indents)
        checker.indents.append(most_common)
        yield
        checker.indents.pop()
        checker.end_of_node = False


def index_of_first_standalone_comment(node: type[Node]) -> int:
    """
    Get index of first standalone comment.
    Comment can be standalone only if there are not other data statements in the node.
    """
    last_standalone_comment = len(node.body)
    for index, child in enumerate(node.body[::-1], start=-(len(node.body) - 1)):
        if not isinstance(child, (EmptyLine, Comment)):
            return last_standalone_comment
        if isinstance(child, Comment) and get_indent(child) == 0:
            last_standalone_comment = abs(index)
    return last_standalone_comment


class UnevenIndentChecker(VisitorChecker):
    """Checker for indentation violations."""

    bad_indent: BadIndentRule
    bad_block_indent: BadBlockIndentRule

    def __init__(self):
        self.indents = []
        self.parent_indent = 0
        # used to ignore indents from statements in the same line as parent, i.e. Inline IFs
        self.parent_line = 0
        # used to denote end of keyword/test for comments indents
        self.end_of_node = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.indents = []
        self.parent_indent = 0
        self.parent_line = 0
        self.end_of_node = False
        self.generic_visit(node)

    def visit_TestCase(self, node: type[Block]) -> None:  # noqa: N802
        end_index = index_of_first_standalone_comment(node)
        with block_indent(self, node):
            for index, child in enumerate(node.body):
                if index == end_index:
                    self.end_of_node = True
                self.visit(child)

    visit_Keyword = visit_TestCase  # noqa: N815

    def visit_TestCaseSection(self, node) -> None:  # noqa: N802
        self.check_standalone_comments_indent(node)

    def visit_KeywordSection(self, node) -> None:  # noqa: N802
        self.check_standalone_comments_indent(node)

    def check_standalone_comments_indent(self, node) -> None:
        # comments before first test case / keyword
        for child in node.body:
            if (
                getattr(child, "type", "") == Token.COMMENT
                and getattr(child, "tokens", None)
                and child.tokens[0].type == Token.SEPARATOR
            ):
                self.report(
                    self.bad_indent,
                    bad_indent_msg="Line is over-indented",
                    node=child,
                    col=1,
                    end_col=token_col(child, Token.COMMENT),
                )
        self.generic_visit(node)

    def visit_For(self, node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        with block_indent(self, node):
            for child in node.body:
                self.visit(child)
        self.visit_Statement(node.end)

    visit_While = visit_ForLoop = visit_Group = visit_For  # noqa: N815

    def get_common_if_indent(self, node) -> None:
        indents = count_indents(node)
        head = node
        while head.orelse:
            head = head.orelse
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def get_common_try_indent(self, node) -> None:
        indents = count_indents(node)
        head = node
        while head.next:
            head = head.next
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def visit_statements_in_branch(self, node) -> None:
        with replace_parent_indent(self, node):
            for child in node.body:
                self.visit(child)

    def visit_If(self, node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        if node.type == "INLINE IF":
            return
        self.get_common_if_indent(node)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_IfBranch(self, node) -> None:  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)

    def visit_Try(self, node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        self.get_common_try_indent(node)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_TryBranch(self, node) -> None:  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)

    def get_required_indent(self, statement):
        if isinstance(statement, Comment) and self.end_of_node:
            return 0
        if self.bad_indent.indent != -1:
            return self.bad_indent.indent * len(self.indents)
        return self.indents[-1]

    def visit_Statement(self, statement) -> None:  # noqa: N802
        if statement is None or isinstance(statement, EmptyLine) or not self.indents:
            return
        # Ignore indent if current line is on the same line as parent, i.e. test case header or inline IFs
        if self.parent_line == statement.lineno:
            return
        indent = get_indent(statement)
        if self.parent_indent and (indent - 2 < self.parent_indent):
            self.report(
                self.bad_block_indent,
                node=statement,
                col=1,
                end_col=indent + 1,
            )
            return
        req_indent = self.get_required_indent(statement)
        if indent == req_indent:
            return
        over_or_under = "over" if indent > req_indent else "under"
        self.report(
            self.bad_indent,
            bad_indent_msg=f"Line is {over_or_under}-indented",
            node=statement,
            col=1,
            end_col=indent + 1,
        )


class MisalignedContinuation(VisitorChecker, ModelVisitor):
    """Checker for misaligned continuation line markers."""

    misaligned_continuation: MisalignedContinuationRule
    misaligned_continuation_row: MisalignedContinuationRowRule
    # detect if run keyword, but not parse it

    @staticmethod
    def is_inline_if(node):
        return isinstance(node.header, InlineIfHeader)

    def visit_If(self, node) -> None:  # noqa: N802
        # suppress the rules if the multiline-inline-if is already reported
        if ROBOT_VERSION.major >= 5 and self.is_inline_if(node):
            return

    def is_ignorable_run_keyword(self, node) -> bool:
        return (
            self.misaligned_continuation_row.ignore_run_keywords
            and isinstance(node, KeywordCall)
            and is_run_keyword(node.keyword)
        )
        # TODO: test on different version, may lack .keyword

    def visit_Statement(self, node) -> None:  # noqa: N802
        if not node.data_tokens or self.is_ignorable_run_keyword(node):
            return
        starting_row = self.get_indent(node.tokens)
        first_column, indent = 0, 0
        for index, line in enumerate(node.lines):
            if index == 0:
                starting_row = self.get_indent(line)
                if node.type == Token.TAGS:
                    first_column = self.first_line_indent(line, node.type, Token.ARGUMENT)
                continue
            indent = 0
            for token in line:
                if token.type == Token.SEPARATOR:  # count possible indent before or after ...
                    indent += len(token.value.expandtabs(4))
                elif token.type == Token.CONTINUATION:
                    if indent != starting_row:
                        self.report(
                            self.misaligned_continuation,
                            lineno=token.lineno,
                            col=token.col_offset + 1,
                            end_col=token.end_col_offset + 1,
                        )
                        break
                    indent = 0
                elif token.type != Token.EOL and token.value.strip():  # ignore trailing whitespace
                    if node.type == Token.DOCUMENTATION and self.misaligned_continuation_row.ignore_docs:
                        break
                    if first_column:
                        if indent != first_column:
                            cont = [token for token in line if token.type == "CONTINUATION"]
                            if not cont:
                                break
                            self.report(
                                self.misaligned_continuation_row,
                                node=token,
                                end_col=token.col_offset + 1,
                                col=cont[0].end_col_offset + 1,
                            )
                    elif token.type != Token.COMMENT:
                        first_column = indent
                    break  # check only first value

    @staticmethod
    def get_indent(tokens):
        indent_len = 0
        for token in tokens:
            if token.type != Token.SEPARATOR:
                break
            indent_len += len(token.value.expandtabs(4))
        return indent_len

    @staticmethod
    def first_line_indent(tokens, from_tok, search_for):
        """
        Find indent required for other lines to match indentation of first line.

        [from_token]     <search_for>
        ...<-   pos   ->

        :param tokens: statement first line tokens
        :param from_tok: start counting separator after finding from_tok token
        :param search_for: stop counting after finding search_for token
        :return: pos: length of indent
        """
        pos = 0
        found = False
        for token in tokens:
            if not found:
                if token.type == from_tok:
                    found = True
                    # subtract 3 to adjust for ... length in 2nd line
                    pos += len(token.value) - 3
            elif token.type == Token.SEPARATOR:
                pos += len(token.value.expandtabs(4))
            elif token.type == search_for:
                return pos
        return 0  # 0 will ignore first line indent and compare to 2nd line only


class LeftAlignedChecker(VisitorChecker):
    """Checker for left align."""

    variable_not_left_aligned: VariableNotLeftAlignedRule
    suite_setting_not_left_aligned: SuiteSettingNotLeftAlignedRule

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

    def visit_VariableSection(self, node) -> None:  # noqa: N802
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and (token.value == "" or token.value.startswith(" ")):
                if token.value or not child.get_token(Token.ARGUMENT):
                    pos = len(token.value) - len(token.value.lstrip()) + 1
                else:
                    pos = child.get_token(Token.ARGUMENT).col_offset + 1
                self.report(self.variable_not_left_aligned, lineno=token.lineno, col=1, end_col=pos)

    def visit_SettingSection(self, node) -> None:  # noqa: N802
        for child in node.body:
            for error in get_errors(child):
                if "Non-existing setting" in error:
                    self.parse_error(child, error)

    def parse_error(self, node, error) -> None:
        setting_error = re.search("Non-existing setting '(.*)'.", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
        if not setting_error:
            setting_cand = node.get_token(Token.COMMENT)
            if setting_cand and setting_cand.value.replace(" ", "").lower() in self.suite_settings:
                self.report(
                    self.suite_setting_not_left_aligned,
                    node=setting_cand,
                    col=setting_cand.col_offset + 1,
                    end_col=setting_cand.end_col_offset + 1,
                )
        elif not setting_error[0].strip():  # starts with space/tab
            suite_sett_cand = setting_error.replace(" ", "").lower()
            for setting in self.suite_settings:
                if suite_sett_cand.startswith(setting):
                    indent = len(setting_error) - len(setting_error.lstrip())
                    self.report(
                        self.suite_setting_not_left_aligned,
                        node=node,
                        col=indent + 1,
                    )
                    break


class ArgumentsChecker(VisitorChecker):  # TODO merge!!, candidate to check inside rule
    first_argument_in_new_line: FirstArgumentInNewLineRule

    def visit_Arguments(self, node) -> None:  # noqa: N802
        eol_already = None
        for t in node.tokens:
            if t.type == Token.EOL:
                eol_already = t
                continue
            if t.type == Token.ARGUMENT:
                if eol_already is not None:
                    self.report(
                        self.first_argument_in_new_line,
                        argument_name=t.value,
                        lineno=eol_already.lineno,
                        end_lineno=t.lineno,
                        col=eol_already.end_col_offset,
                        end_col=t.end_col_offset,
                    )
                return
