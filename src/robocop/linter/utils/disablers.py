"""Collection of classes for detecting checker disablers (like # robocop: off) in robot files"""

from __future__ import annotations

import re
from collections import defaultdict
from copy import deepcopy
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import CommentSection

try:
    from robot.api.parsing import ModelVisitor
except ImportError:
    from robot.parsing.model.visitor import ModelVisitor


if TYPE_CHECKING:
    from robot.parsing import File
    from robot.parsing.model import KeywordSection, Statement, TestCaseSection
    from robot.parsing.model.statements import Comment, KeywordName, Node, TestCaseName

    from robocop.linter.diagnostics import Diagnostic


class DisablersInFile:  # pylint: disable=too-few-public-methods
    """Container for file disablers"""

    def __init__(self, blocks: list | None = None):
        self.lastblock = -1
        self.lines = set()
        self.blocks = blocks if blocks else []

    def copy(self) -> DisablersInFile:
        return deepcopy(self)


class DisablersVisitor(ModelVisitor):
    def __init__(self, model: File):
        self.file_disabled = False
        self.file_end = 1
        self.is_first_comment_section = True
        self.keyword_or_test_section = False
        self.last_name_header_line = 0
        self.disablers_in_scope = []
        self.disabler_pattern = re.compile(r"robocop: ?(?P<disabler>off|on) ?=?(?P<rules>[\w\-,]*)")
        self.rules = defaultdict(DisablersInFile().copy)
        self.visit(model)

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.file_end = node.end_lineno
        self.generic_visit(node)

    def parse_disablers_in_node(self, node: type[Node], last_line: int | None = None) -> None:
        self.disablers_in_scope.append(defaultdict(DisablersInFile().copy))
        self.generic_visit(node)
        for rule_name, rule_disabler in self.disablers_in_scope[-1].items():
            if self.is_first_comment_section:
                if rule_name == "all":
                    self.file_disabled = True
                self.rules[rule_name] = DisablersInFile(blocks=[(1, self.file_end)])
            else:
                last_line = node.end_lineno if last_line is None else last_line
                self._end_block(self.disablers_in_scope[-1], rule_name, last_line)
                self.rules[rule_name].blocks.extend(rule_disabler.blocks)
                self.rules[rule_name].lines.update(rule_disabler.lines)
        self.disablers_in_scope.pop()

    def visit_KeywordSection(self, node: KeywordSection | TestCaseSection) -> None:  # noqa: N802
        self.keyword_or_test_section = True
        self.parse_disablers_in_node(node)
        self.keyword_or_test_section = False

    visit_TestCaseSection = visit_KeywordSection  # noqa: N815

    def visit_Section(self, node: type[Node]) -> None:  # noqa: N802
        self.is_first_comment_section = self.is_first_comment_section and isinstance(node, CommentSection)
        self.parse_disablers_in_node(node)
        self.is_first_comment_section = False

    visit_TestCase = visit_Keyword = visit_Try = visit_For = visit_ForLoop = visit_While = visit_Group = visit_Section  # noqa: N815

    def visit_If(self, node: type[Node]) -> None:  # noqa: N802
        last_line = node.body[-1].end_lineno if node.body else None
        self.parse_disablers_in_node(node, last_line)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        for comment in node.get_tokens(Token.COMMENT):
            self.parse_comment_token(comment, is_inline=True)

    def visit_TestCaseName(self, node: KeywordName | TestCaseName) -> None:  # noqa: N802
        """Save last test case / keyword header line number to check if comment is standalone."""
        self.last_name_header_line = node.lineno
        self.visit_Statement(node)

    visit_KeywordName = visit_TestCaseName  # noqa: N815

    def visit_Comment(self, node: Comment) -> None:  # noqa: N802
        for comment in node.get_tokens(Token.COMMENT):
            # Comment is only inline if it is next to test/kw name
            is_inline = comment.lineno == self.last_name_header_line
            self.parse_comment_token(comment, is_inline=is_inline)

    def parse_comment_token(self, token: Token, is_inline: bool) -> None:
        if "#" not in token.value:
            return
        if "# noqa" in token.value:
            self._add_inline_disabler("all", token.lineno)
        disabler = self.disabler_pattern.search(token.value)
        if not disabler:
            return
        if not disabler.group("rules"):
            rules = ["all"]
        else:
            rules = [rule.strip() for rule in disabler.group("rules").split(",") if rule.strip()]
        if disabler.group("disabler") == "off":
            for rule in rules:
                if is_inline:
                    self._add_inline_disabler(rule, token.lineno)
                else:
                    scope = self.get_scope_for_disabler(token)
                    self._start_block(scope, rule, token.lineno)
        elif disabler.group("disabler") == "on" and not is_inline:
            scope = self.get_scope_for_disabler(token)
            for rule in rules:
                self._end_block(scope, rule, token.lineno)

    def get_scope_for_disabler(self, token: Token) -> defaultdict[DisablersInFile]:
        if token.col_offset == 0 and self.keyword_or_test_section:
            return self.disablers_in_scope[0]
        return self.disablers_in_scope[-1]

    def _add_inline_disabler(self, rule: str, lineno: int) -> None:
        self.rules[rule].lines.add(lineno)

    def _start_block(self, scope: defaultdict[DisablersInFile], rule: str, lineno: int) -> None:
        if scope[rule].lastblock == -1:
            scope[rule].lastblock = lineno

    def _end_block(self, scope: defaultdict[DisablersInFile], rule: str, lineno: int) -> None:
        if rule == "all":
            self._end_all_blocks(scope, lineno)
        if rule not in scope:
            return
        if scope[rule].lastblock != -1:
            block = (scope[rule].lastblock, lineno)
            scope[rule].lastblock = -1
            scope[rule].blocks.append(block)

    def _end_all_blocks(self, scope: defaultdict[DisablersInFile], lineno: int) -> None:
        for rule in scope:
            if rule == "all":
                continue  # to avoid recursion
            self._end_block(scope, rule, lineno)


class DisablersFinder(ModelVisitor):
    """Visit and find robocop disablers in Robot Framework file."""

    def __init__(self, model: File):
        self.disabled = DisablersVisitor(model)

    @property
    def any_disabler(self) -> bool:
        return len(self.disabled.rules) != 0

    @property
    def file_disabled(self) -> bool:
        return self.disabled.file_disabled

    def is_rule_disabled(self, diagnostic: Diagnostic) -> bool:
        """
        Check if given `rule_msg` is disabled.

        'All' takes precedence, then line disablers, then block disablers.
        We're checking for both message id and name.
        """
        if not self.any_disabler:
            return False
        return any(
            self.is_line_disabled(line, rule)
            for line in (diagnostic.range.start.line, *diagnostic.extended_disablers)
            for rule in ("all", diagnostic.rule.rule_id, diagnostic.rule.name)
        )

    def is_line_disabled(self, line: int, rule: str) -> bool:
        """Check if given line is in range of any disabled block"""
        if rule not in self.disabled.rules:
            return False
        if line in self.disabled.rules[rule].lines:
            return True
        return any(block[0] <= line <= block[1] for block in self.disabled.rules[rule].blocks)
