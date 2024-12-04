"""Spacing checkers"""

import re
from collections import Counter
from contextlib import contextmanager

from robot.api import Token
from robot.parsing.model.blocks import Keyword, TestCase
from robot.parsing.model.statements import Comment, EmptyLine, KeywordCall
from robot.parsing.model.visitor import ModelVisitor

from robocop.utils.misc import ROBOT_VERSION

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import DefaultRule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.utils import get_errors, get_section_name, str2bool, token_col
from robocop.utils.run_keywords import is_run_keyword

RULE_CATEGORY_ID = "10"

rules = {
    "1001": DefaultRule(
        rule_id="1001",
        name="trailing-whitespace",
        msg="Trailing whitespace at the end of line",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
    ),
    "1002": DefaultRule(
        rule_id="1002",
        name="missing-trailing-blank-line",
        msg="Missing trailing blank line at the end of file",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
    ),
    "1003": DefaultRule(
        RuleParam(
            name="empty_lines",
            default=2,
            converter=int,
            desc="number of empty lines required between sections",
        ),
        rule_id="1003",
        name="empty-lines-between-sections",
        msg="Invalid number of empty lines between sections ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
    ),
    "1004": DefaultRule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between test cases",
        ),
        rule_id="1004",
        name="empty-lines-between-test-cases",
        msg="Invalid number of empty lines between test cases ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
    ),
    "1005": DefaultRule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of empty lines required between keywords",
        ),
        rule_id="1005",
        name="empty-lines-between-keywords",
        msg="Invalid number of empty lines between keywords ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        added_in_version="1.0.0",
    ),
    "1006": DefaultRule(
        rule_id="1006",
        name="mixed-tabs-and-spaces",
        msg="Inconsistent use of tabs and spaces in file",
        severity=RuleSeverity.WARNING,
        added_in_version="1.1.0",
    ),
    "1008": DefaultRule(
        RuleParam(
            name="indent",
            default=-1,
            converter=int,
            desc="Number of spaces per indentation level",
        ),
        rule_id="1008",
        name="bad-indent",
        msg="{{ bad_indent_msg }}",
        severity=RuleSeverity.WARNING,
        docs="""
        Line is misaligned or indent is invalid.

        This rule reports warning if the line is misaligned in the current block. Example of rule violation::

            *** Keywords ***
            Keyword
                Keyword Call
                 Misaligned Keyword Call  # line is over-intended by one space
                IF    $condition    RETURN
               Keyword Call  # line is under-intended by two spaces

        The correct indentation is determined by the most common indentation in the current block. Although,
        it allows for more flexible indentation by specifying the ``indent`` parameter for checking if the
        indentation is the multiple of ``indent`` spaces (default -1, which makes this parameter being ignored).
        """,
        added_in_version="3.0.0",
    ),
    "1009": DefaultRule(
        RuleParam(
            name="empty_lines",
            default=0,
            converter=int,
            desc="number of empty lines allowed after section header",
        ),
        SeverityThreshold("empty_lines", substitute_value="allowed_empty_lines"),
        rule_id="1009",
        name="empty-line-after-section",
        msg="Too many empty lines after '{{ section_name }}' section header "
        "({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Empty lines after the section header are not allowed by default. Example of rule violation::

             *** Test Cases ***

             Resource  file.resource

        It can be configured using ``empty_lines`` parameter.
        """,
        added_in_version="1.2.0",
    ),
    "1010": DefaultRule(
        rule_id="1010",
        name="too-many-trailing-blank-lines",
        msg="Too many blank lines at the end of file",
        severity=RuleSeverity.WARNING,
        docs="""There should be exactly one blank line at the end of the file""",
        added_in_version="1.4.0",
    ),
    "1011": DefaultRule(
        rule_id="1011",
        name="misaligned-continuation",
        msg="Continuation marker should be aligned with starting row",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

                Default Tags       default tag 1    default tag 2    default tag 3
            ...                default tag 4    default tag 5

                *** Test Cases ***
                Example
                    Do X    first argument    second argument    third argument
                  ...    fourth argument    fifth argument    sixth argument

        """,
        added_in_version="1.6.0",
    ),
    "1012": DefaultRule(
        RuleParam(
            name="empty_lines",
            default=1,
            converter=int,
            desc="number of allowed consecutive empty lines",
        ),
        SeverityThreshold("empty_lines", compare_method="greater", substitute_value="allowed_empty_lines"),
        rule_id="1012",
        name="consecutive-empty-lines",
        msg="Too many consecutive empty lines ({{ empty_lines }}/{{ allowed_empty_lines }})",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

            *** Variables ***
            ${VAR}    value


            ${VAR2}    value  # previous line will be reported with 2/1 consecutive lines


            *** Keywords ***
            Keyword
                Step 1


                Step 2  # previous line will be reported with 2/1 consecutive lines

        """,
        added_in_version="1.8.0",
    ),
    "1013": DefaultRule(
        rule_id="1013",
        name="empty-lines-in-statement",
        msg="Multi-line statement with empty lines",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

             Keyword
             ...  1
             # empty line in-between multiline statement
             ...  2

        """,
        added_in_version="1.8.0",
    ),
    "1014": DefaultRule(
        rule_id="1014",
        name="variable-should-be-left-aligned",
        msg="Variable in Variable section should be left aligned",
        severity=RuleSeverity.ERROR,
        version=">=4.0",
        docs="""
        Example of rule violation::

            *** Variables ***
             ${VAR}  1
              ${VAR2}  2

        """,
        added_in_version="1.8.0",
    ),
    "1015": DefaultRule(
        RuleParam(name="ignore_docs", default=True, converter=str2bool, show_type="bool", desc="Ignore documentation"),
        RuleParam(
            name="ignore_run_keywords", default=False, converter=str2bool, show_type="bool", desc="Ignore run keywords"
        ),
        rule_id="1015",
        name="misaligned-continuation-row",
        msg="Each next continuation line should be aligned with the previous one",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

            *** Variable ***
            ${VAR}    This is a long string.
            ...       It has multiple sentences.
            ...         And this line is misaligned with previous one.

            *** Test Cases ***
            My Test
                My Keyword
                ...    arg1
                ...   arg2  # misaligned
        """,
        added_in_version="1.11.0",
    ),
    "1016": DefaultRule(
        rule_id="1016",
        name="suite-setting-should-be-left-aligned",
        msg="Setting in Settings section should be left aligned",
        severity=RuleSeverity.ERROR,
        version=">=4.0",
        docs="""
        Example of rule violation::

            *** Settings ***
                Library  Collections
                Resource  data.resource
                Variables  vars.robot

        """,
        added_in_version="2.4.0",
    ),
    "1017": DefaultRule(
        rule_id="1017",
        name="bad-block-indent",
        msg="Indent expected. Provide 2 or more spaces of indentation for statements inside block",
        severity=RuleSeverity.ERROR,
        docs="""
        If the indentation is less than two spaces than current block parent element
        (such as ``FOR``/``IF``/``WHILE``/``TRY`` header) the indentation is invalid and the rule reports an error::

            *** Keywords ***
            Some Keyword
                FOR  ${elem}  IN  ${list}
                    Log  ${elem}  # this is fine
               Log  stuff    # this is bad indent
            # bad comment
                END
        """,
        added_in_version="3.0.0",
    ),
    "1018": DefaultRule(
        rule_id="1018",
        name="first-argument-in-new-line",
        msg="First argument: '{{ argument_name }}' should be placed on the same line as [Arguments] setting",
        severity=RuleSeverity.WARNING,
        added_in_version="5.3.0",
        docs="""
        Example of rule violation::

            *** Keywords ***
            Custom Keyword With Five Required Arguments
            [Arguments]
            ...    ${name}
            ...    ${surname}

        """,
    ),
}


class InvalidSpacingChecker(RawFileChecker):
    """Checker for trailing spaces and lines."""

    reports = (
        "trailing-whitespace",
        "missing-trailing-blank-line",
        "too-many-trailing-blank-lines",
    )

    def __init__(self):
        self.raw_lines = []
        super().__init__()

    def parse_file(self):
        self.raw_lines = []
        super().parse_file()
        if self.raw_lines:
            last_line = self.raw_lines[-1]
            if last_line in ["\n", "\r", "\r\n"]:
                self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines) + 1, end_col=len(last_line) + 1)
                return
            empty_lines = 0
            for line in self.raw_lines[::-1]:
                if not line.strip():
                    empty_lines += 1
                else:
                    break
                if empty_lines > 1:
                    self.report("too-many-trailing-blank-lines", lineno=len(self.raw_lines), end_col=len(last_line) + 1)
                    return
            if not empty_lines and not last_line.endswith(("\n", "\r")):
                self.report("missing-trailing-blank-line", lineno=len(self.raw_lines), end_col=len(last_line) + 1)

    def check_line(self, line, lineno):
        self.raw_lines.append(line)

        stripped_line = line.rstrip("\n\r")
        if stripped_line and stripped_line[-1] in [" ", "\t"]:
            self.report("trailing-whitespace", lineno=lineno, col=len(stripped_line))


class EmptyLinesChecker(VisitorChecker):
    """Checker for invalid spacing."""

    reports = (
        "empty-lines-between-sections",
        "empty-lines-between-test-cases",
        "empty-lines-between-keywords",
        "empty-line-after-section",
        "consecutive-empty-lines",
        "empty-lines-in-statement",
    )

    def verify_consecutive_empty_lines(self, lines, check_leading=True, check_trailing=False):
        allowed_consecutive = self.param("consecutive-empty-lines", "empty_lines")
        empty_lines = 0
        last_empty_line = None
        data_found = check_leading
        for i, line in enumerate(lines):
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
                        "consecutive-empty-lines",
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
                "consecutive-empty-lines",
                empty_lines=empty_lines,
                allowed_empty_lines=allowed_consecutive,
                node=last_empty_line,
                sev_threshold_value=empty_lines,
                col=1,
                lineno=last_empty_line.lineno - empty_lines + 1,
                end_lineno=last_empty_line.lineno,
            )
        return empty_lines

    def check_empty_lines_in_keyword_test(self, node):
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

    def visit_Statement(self, node):  # noqa: N802
        prev_token = None
        for token in node.tokens:
            if token.type == Token.EOL:
                if prev_token:
                    self.report("empty-lines-in-statement", node=token)
                prev_token = token
            else:
                prev_token = None

    def visit_VariableSection(self, node):  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def visit_SettingSection(self, node):  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def verify_empty_lines_between_nodes(self, node, node_type, issue_name, allowed_empty_lines):
        last_index = len(node.body) - 1
        for index, child in enumerate(node.body):
            if not isinstance(child, node_type):
                continue
            empty_lines = self.check_empty_lines_in_keyword_test(child)
            if allowed_empty_lines not in (empty_lines, -1) and index < last_index:
                self.report(
                    issue_name,
                    empty_lines=empty_lines,
                    allowed_empty_lines=allowed_empty_lines,
                    lineno=child.end_lineno,
                    end_lineno=child.end_lineno + 1,
                    end_col=len(child.name) + 1,
                )
        self.generic_visit(node)

    def visit_TestCaseSection(self, node):  # noqa: N802
        allowed_lines = -1 if self.templated_suite else self.param("empty-lines-between-test-cases", "empty_lines")
        self.verify_empty_lines_between_nodes(node, TestCase, "empty-lines-between-test-cases", allowed_lines)

    def visit_KeywordSection(self, node):  # noqa: N802
        self.verify_empty_lines_between_nodes(
            node,
            Keyword,
            "empty-lines-between-keywords",
            self.param("empty-lines-between-keywords", "empty_lines"),
        )

    def visit_For(self, node):  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_trailing=True)
        self.generic_visit(node)

    visit_ForLoop = visit_While = visit_Try = visit_If = visit_For  # noqa: N815

    def visit_File(self, node):  # noqa: N802
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
            if empty_lines != self.param("empty-lines-between-sections", "empty_lines"):
                self.report(
                    "empty-lines-between-sections",
                    empty_lines=empty_lines,
                    allowed_empty_lines=self.param("empty-lines-between-sections", "empty_lines"),
                    lineno=section.end_lineno,
                    col=1,
                    end_col=child.end_col_offset,
                )
        super().visit_File(node)

    def check_empty_lines_after_section(self, section):
        empty_lines = []
        for child in section.body:
            if not isinstance(child, EmptyLine):
                break
            empty_lines.append(child)
        else:
            return
        if len(empty_lines) > self.param("empty-line-after-section", "empty_lines"):
            self.report(
                "empty-line-after-section",
                section_name=get_section_name(section),
                empty_lines=len(empty_lines),
                allowed_empty_lines=self.param("empty-line-after-section", "empty_lines"),
                node=empty_lines[-1],
                sev_threshold_value=len(empty_lines),
                lineno=section.lineno,
                end_col=len(get_section_name(section)) + 1,
            )


class InconsistentUseOfTabsAndSpacesChecker(VisitorChecker, ModelVisitor):
    """Checker for inconsistent use of tabs and spaces."""

    reports = ("mixed-tabs-and-spaces",)

    def __init__(self):
        self.found, self.tabs, self.spaces = False, False, False
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.found, self.tabs, self.spaces = False, False, False
        super().visit_File(node)

    def visit_Statement(self, node):  # noqa: N802
        if self.found:
            return
        for token in node.get_tokens(Token.SEPARATOR):
            self.tabs = "\t" in token.value or self.tabs
            self.spaces = " " in token.value or self.spaces

            if self.tabs and self.spaces:
                self.report("mixed-tabs-and-spaces", node=node, lineno=1)
                self.found = True
                break


def get_indent(node):
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


def count_indents(node):
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


def most_common_indent(indents):
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
def replace_parent_indent(checker, node):
    """Temporarily replace parent indent with current node indent."""
    parent_line = checker.parent_line
    parent_indent = checker.parent_indent
    checker.parent_indent = get_indent(node)
    checker.parent_line = node.lineno
    yield
    checker.parent_indent = parent_indent
    checker.parent_line = parent_line


@contextmanager
def block_indent(checker, node):
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


def index_of_first_standalone_comment(node):
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

    reports = ("bad-indent", "bad-block-indent")

    def __init__(self):
        self.indents = []
        self.parent_indent = 0
        # used to ignore indents from statements in the same line as parent, i.e. Inline IFs
        self.parent_line = 0
        # used to denote end of keyword/test for comments indents
        self.end_of_node = False
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.indents = []
        self.parent_indent = 0
        self.parent_line = 0
        self.end_of_node = False
        self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa: N802
        end_index = index_of_first_standalone_comment(node)
        with block_indent(self, node):
            for index, child in enumerate(node.body):
                if index == end_index:
                    self.end_of_node = True
                self.visit(child)

    visit_Keyword = visit_TestCase  # noqa: N815

    def visit_TestCaseSection(self, node):  # noqa: N802
        self.check_standalone_comments_indent(node)

    def visit_KeywordSection(self, node):  # noqa: N802
        self.check_standalone_comments_indent(node)

    def check_standalone_comments_indent(self, node):
        # comments before first test case / keyword
        for child in node.body:
            if (
                getattr(child, "type", "") == Token.COMMENT
                and getattr(child, "tokens", None)
                and child.tokens[0].type == Token.SEPARATOR
            ):
                self.report(
                    "bad-indent",
                    bad_indent_msg="Line is over-indented",
                    node=child,
                    col=1,
                    end_col=token_col(child, Token.COMMENT),
                )
        self.generic_visit(node)

    def visit_For(self, node):  # noqa: N802
        self.visit_Statement(node.header)
        with block_indent(self, node):
            for child in node.body:
                self.visit(child)
        self.visit_Statement(node.end)

    visit_While = visit_ForLoop = visit_For  # noqa: N815

    def get_common_if_indent(self, node):
        indents = count_indents(node)
        head = node
        while head.orelse:
            head = head.orelse
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def get_common_try_indent(self, node):
        indents = count_indents(node)
        head = node
        while head.next:
            head = head.next
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def visit_statements_in_branch(self, node):
        with replace_parent_indent(self, node):
            for child in node.body:
                self.visit(child)

    def visit_If(self, node):  # noqa: N802
        self.visit_Statement(node.header)
        if node.type == "INLINE IF":
            return
        self.get_common_if_indent(node)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_IfBranch(self, node):  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)

    def visit_Try(self, node):  # noqa: N802
        self.visit_Statement(node.header)
        self.get_common_try_indent(node)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_TryBranch(self, node):  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)

    def get_required_indent(self, statement):
        if isinstance(statement, Comment) and self.end_of_node:
            return 0
        if self.param("bad-indent", "indent") != -1:
            return self.param("bad-indent", "indent") * len(self.indents)
        return self.indents[-1]

    def visit_Statement(self, statement):  # noqa: N802
        if statement is None or isinstance(statement, EmptyLine) or not self.indents:
            return
        # Ignore indent if current line is on the same line as parent, i.e. test case header or inline IFs
        if self.parent_line == statement.lineno:
            return
        indent = get_indent(statement)
        if self.parent_indent and (indent - 2 < self.parent_indent):
            self.report(
                "bad-block-indent",
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
            "bad-indent",
            bad_indent_msg=f"Line is {over_or_under}-indented",
            node=statement,
            col=1,
            end_col=indent + 1,
        )


class MisalignedContinuation(VisitorChecker, ModelVisitor):
    """Checker for misaligned continuation line markers."""

    reports = (
        "misaligned-continuation",
        "misaligned-continuation-row",
    )
    # detect if run keyword, but not parse it

    @staticmethod
    def is_inline_if(node):
        return isinstance(node.header, InlineIfHeader)

    def visit_If(self, node):  # noqa: N802
        # suppress the rules if the multiline-inline-if is already reported
        if ROBOT_VERSION.major >= 5 and self.is_inline_if(node):
            return

    def is_ignorable_run_keyword(self, node) -> bool:
        return (
            isinstance(node, KeywordCall)
            and self.param("misaligned-continuation-row", "ignore_run_keywords")
            and is_run_keyword(node.keyword)
        )
        # TODO: test on different version, may lack .keyword

    def visit_Statement(self, node):  # noqa: N802
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
                            "misaligned-continuation",
                            lineno=token.lineno,
                            col=token.col_offset + 1,
                            end_col=token.end_col_offset + 1,
                        )
                        break
                    indent = 0
                elif token.type != Token.EOL and token.value.strip():  # ignore trailing whitespace
                    ignore_docs = self.param("misaligned-continuation-row", "ignore_docs")
                    if node.type == Token.DOCUMENTATION and ignore_docs:
                        break
                    if first_column:
                        if indent != first_column:
                            cont = [token for token in line if token.type == "CONTINUATION"]
                            if not cont:
                                break
                            self.report(
                                "misaligned-continuation-row",
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

    reports = (
        "variable-should-be-left-aligned",
        "suite-setting-should-be-left-aligned",
    )

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

    def visit_VariableSection(self, node):  # noqa: N802
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and (token.value == "" or token.value.startswith(" ")):
                if token.value or not child.get_token(Token.ARGUMENT):
                    pos = len(token.value) - len(token.value.lstrip()) + 1
                else:
                    pos = child.get_token(Token.ARGUMENT).col_offset + 1
                self.report("variable-should-be-left-aligned", lineno=token.lineno, col=1, end_col=pos)

    def visit_SettingSection(self, node):  # noqa: N802
        for child in node.body:
            for error in get_errors(child):
                if "Non-existing setting" in error:
                    self.parse_error(child, error)

    def parse_error(self, node, error):
        setting_error = re.search("Non-existing setting '(.*)'.", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
        if not setting_error:
            setting_cand = node.get_token(Token.COMMENT)
            if setting_cand and setting_cand.value.replace(" ", "").lower() in self.suite_settings:
                self.report(
                    "suite-setting-should-be-left-aligned",
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
                        "suite-setting-should-be-left-aligned",
                        node=node,
                        col=indent + 1,
                    )
                    break


class ArgumentsChecker(VisitorChecker):
    reports = ("first-argument-in-new-line",)

    def visit_Arguments(self, node):  # noqa: N802
        eol_already = None
        for t in node.tokens:
            if t.type == Token.EOL:
                eol_already = t
                continue
            if t.type == Token.ARGUMENT:
                if eol_already is not None:
                    self.report(
                        "first-argument-in-new-line",
                        argument_name=t.value,
                        lineno=eol_already.lineno,
                        end_lineno=t.lineno,
                        col=eol_already.end_col_offset,
                        end_col=t.end_col_offset,
                    )
                return
