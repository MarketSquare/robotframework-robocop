"""Checkers for the rules defined in ``robocop.linter.rules.spacing``."""

from __future__ import annotations

from contextlib import contextmanager
from itertools import takewhile
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import Keyword, TestCase
from robot.parsing.model.statements import Comment, EmptyLine, KeywordCall

from robocop.linter.rules import Rule, VisitorChecker, spacing
from robocop.linter.rules.spacing import (
    count_indents,
    get_indent,
    index_of_first_standalone_comment,
    most_common_indent,
)
from robocop.linter.utils.misc import get_section_name, token_col
from robocop.parsing.run_keywords import is_run_keyword
from robocop.version_handling import INLINE_IF_SUPPORTED

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robot.parsing import File
    from robot.parsing.model import Block, Section
    from robot.parsing.model.statements import Node, Statement


@contextmanager
def replace_parent_indent(checker: UnevenIndentChecker, node: Node) -> Iterator[None]:
    """Temporarily replace parent indent with current node indent."""
    parent_line = checker.parent_line
    parent_indent = checker.parent_indent
    checker.parent_indent = get_indent(node)
    checker.parent_line = node.lineno
    yield
    checker.parent_indent = parent_indent
    checker.parent_line = parent_line


@contextmanager
def block_indent(checker: UnevenIndentChecker, node: Node) -> Iterator[None]:
    """Temporarily replace parent indent and store current node indents in the stack."""
    with replace_parent_indent(checker, node):
        indents = count_indents(node)
        most_common = most_common_indent(indents)
        checker.indents.append(most_common)
        yield
        checker.indents.pop()
        checker.end_of_node = False


class EmptyLinesChecker(VisitorChecker):
    """Checker for invalid spacing."""

    empty_lines_between_sections: spacing.EmptyLinesBetweenSectionsRule
    empty_lines_between_test_cases: spacing.EmptyLinesBetweenTestCasesRule
    empty_lines_between_keywords: spacing.EmptyLinesBetweenKeywordsRule
    empty_line_after_section: spacing.EmptyLineAfterSectionRule
    consecutive_empty_lines: spacing.ConsecutiveEmptyLinesRule
    empty_lines_in_statement: spacing.EmptyLinesInStatementRule
    empty_line_in_test_template: spacing.EmptyLineInTestTemplateRule
    empty_lines_inside_block: spacing.EmptyLinesInsideBlockRule

    def verify_consecutive_empty_lines(
        self, lines: list[Node], check_leading: bool = True, check_trailing: bool = False
    ) -> int:
        allowed_consecutive = self.consecutive_empty_lines.empty_lines
        empty_lines = 0
        last_empty_line: EmptyLine | None = None
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
                if empty_lines > allowed_consecutive and last_empty_line is not None:  # and i != len(lines)-1:
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
        if check_trailing and empty_lines > allowed_consecutive and last_empty_line is not None:
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

    def check_empty_lines_in_keyword_test(self, node: Node) -> int:
        """
        Verify number of consecutive empty lines inside keyword or test.

        Return number of trailing empty lines.
        """
        # split node and trailing empty lines/comments
        end_found = False
        node_lines: list[Node] = []
        trailing_lines: list[Node] = []
        for child in node.body[::-1]:
            if not end_found and isinstance(child, (EmptyLine, Comment)):
                trailing_lines.append(child)
            else:
                end_found = True
                node_lines.append(child)
        self.verify_consecutive_empty_lines(list(reversed(node_lines)))
        return self.verify_consecutive_empty_lines(list(reversed(trailing_lines)))

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        prev_token = None
        for token in node.tokens:
            if token.type == Token.EOL:
                if prev_token:
                    self.report(self.empty_lines_in_statement, node=token)
                prev_token = token
            else:
                prev_token = None

    def visit_VariableSection(self, node: Node) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def visit_SettingSection(self, node: Node) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_leading=False)
        self.generic_visit(node)

    def verify_empty_lines_between_nodes(
        self, node: Node, node_type: type[Node], rule: Rule, allowed_empty_lines: int
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

    def visit_TestCaseSection(self, node: Node) -> None:  # noqa: N802
        allowed_lines = -1 if self.templated_suite else self.empty_lines_between_test_cases.empty_lines
        self.verify_empty_lines_between_nodes(node, TestCase, self.empty_lines_between_test_cases, allowed_lines)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.empty_line_in_test_template.check(node)
        self.generic_visit(node)

    def visit_KeywordSection(self, node: Node) -> None:  # noqa: N802
        self.verify_empty_lines_between_nodes(
            node,
            Keyword,
            self.empty_lines_between_keywords,
            self.empty_lines_between_keywords.empty_lines,
        )

    def visit_For(self, node: Node) -> None:  # noqa: N802
        self.verify_consecutive_empty_lines(node.body, check_trailing=True)
        self.verify_empty_lines_inside_block(node)
        self.generic_visit(node)

    visit_ForLoop = visit_While = visit_Try = visit_If = visit_Group = visit_For  # noqa: N815

    def verify_empty_lines_inside_block(self, node: Node) -> None:
        allowed = self.empty_lines_inside_block.empty_lines
        body = node.body
        if not body:
            return
        leading = list(takewhile(lambda line: isinstance(line, EmptyLine), body))
        all_empty = len(leading) == len(body)
        if len(leading) > allowed:
            self.report_empty_lines_inside_block(leading, "after block header")
        if not all_empty:
            trailing = list(takewhile(lambda line: isinstance(line, EmptyLine), reversed(body)))
            if len(trailing) > allowed:
                trailing.reverse()
                self.report_empty_lines_inside_block(trailing, "before block end")

    def report_empty_lines_inside_block(self, empty_lines: list[EmptyLine], block_position: str) -> None:
        allowed = self.empty_lines_inside_block.empty_lines
        self.report(
            self.empty_lines_inside_block,
            block_position=block_position,
            empty_lines=len(empty_lines),
            allowed_empty_lines=allowed,
            node=empty_lines[0],
            lineno=empty_lines[0].lineno,
            end_lineno=empty_lines[-1].lineno,
            col=1,
            sev_threshold_value=len(empty_lines),
        )

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
                extra_lines = empty_lines - self.empty_lines_between_sections.empty_lines - 1
                self.report(
                    self.empty_lines_between_sections,
                    empty_lines=empty_lines,
                    allowed_empty_lines=self.empty_lines_between_sections.empty_lines,
                    lineno=section.end_lineno - (extra_lines + 1 if extra_lines > 0 else 0),
                    end_lineno=section.end_lineno,
                    col=1,
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

    mixed_tabs_and_spaces: spacing.MixedTabsAndSpacesRule

    def __init__(self) -> None:
        self.tabs: list[Token] = []
        self.spaces: list[Token] = []
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.tabs = []
        self.spaces = []
        super().visit_File(node)
        if self.tabs and self.spaces:
            less_popular = self.tabs if len(self.tabs) < len(self.spaces) else self.spaces
            for token in less_popular:
                self.report(
                    self.mixed_tabs_and_spaces,
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset,
                )

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        for token in node.get_tokens(Token.SEPARATOR):
            if "\t" in token.value:
                self.tabs.append(token)
            elif " " in token.value:
                self.spaces.append(token)


class UnevenIndentChecker(VisitorChecker):
    """Checker for indentation violations."""

    bad_indent: spacing.BadIndentRule
    bad_block_indent: spacing.BadBlockIndentRule

    def __init__(self) -> None:
        self.indents: list[int] = []
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

    def visit_TestCaseSection(self, node: Node) -> None:  # noqa: N802
        if self.templated_suite:
            return
        self.check_standalone_comments_indent(node)

    def visit_KeywordSection(self, node: Node) -> None:  # noqa: N802
        self.check_standalone_comments_indent(node)

    def check_standalone_comments_indent(self, node: Node) -> None:
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

    def visit_For(self, node: Node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        with block_indent(self, node):
            for child in node.body:
                self.visit(child)
        self.visit_Statement(node.end)

    visit_While = visit_ForLoop = visit_Group = visit_For  # noqa: N815

    def get_common_if_indent(self, node: Node) -> None:
        indents = count_indents(node)
        head = node
        while head.orelse:
            head = head.orelse
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def get_common_try_indent(self, node: Node) -> None:
        indents = count_indents(node)
        head = node
        while head.next:
            head = head.next
            indents += count_indents(head)
        most_common = most_common_indent(indents)
        self.indents.append(most_common)

    def visit_statements_in_branch(self, node: Node) -> None:
        with replace_parent_indent(self, node):
            for child in node.body:
                self.visit(child)

    def visit_If(self, node: Node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        if node.type == "INLINE IF":
            return
        self.get_common_if_indent(node)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_IfBranch(self, node: Node) -> None:  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.orelse is not None:
            self.visit_IfBranch(node.orelse)

    def visit_Try(self, node: Node) -> None:  # noqa: N802
        self.visit_Statement(node.header)
        self.get_common_try_indent(node)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)
        self.indents.pop()
        self.visit_Statement(node.end)

    def visit_TryBranch(self, node: Node) -> None:  # noqa: N802
        indent = self.indents.pop()
        self.visit_Statement(node.header)
        self.indents.append(indent)
        self.visit_statements_in_branch(node)
        if node.next is not None:
            self.visit_TryBranch(node.next)

    def get_required_indent(self, statement: Statement) -> int:
        if isinstance(statement, Comment) and self.end_of_node:
            return 0
        if self.bad_indent.indent != -1:
            return int(self.bad_indent.indent) * len(self.indents)
        return self.indents[-1]

    def visit_Statement(self, statement: Statement) -> None:  # noqa: N802
        if statement is None or isinstance(statement, EmptyLine) or not self.indents:
            return
        # Ignore indent if the current line is on the same line as a parent, i.e. test case header or inline IFs
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


class MisalignedContinuation(VisitorChecker):
    """Checker for misaligned continuation line markers."""

    misaligned_continuation: spacing.MisalignedContinuationRule
    misaligned_continuation_row: spacing.MisalignedContinuationRowRule
    # detect if run keyword, but not parse it

    @staticmethod
    def is_inline_if(node: Node) -> bool:
        return isinstance(node.header, InlineIfHeader)

    def visit_If(self, node: Node) -> None:  # noqa: N802
        # suppress the rules if the multiline-inline-if is already reported
        if INLINE_IF_SUPPORTED and self.is_inline_if(node):
            return

    def is_ignorable_run_keyword(self, node: Node) -> bool:
        return (
            self.misaligned_continuation_row.ignore_run_keywords
            and isinstance(node, KeywordCall)
            and is_run_keyword(node.keyword)
        )
        # TODO: test on different version, may lack .keyword

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
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
    def get_indent(tokens: list[Token]) -> int:
        indent_len = 0
        for token in tokens:
            if token.type != Token.SEPARATOR:
                break
            indent_len += len(token.value.expandtabs(4))
        return indent_len

    @staticmethod
    def first_line_indent(tokens: list[Token], from_tok: str, search_for: str) -> int:
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
