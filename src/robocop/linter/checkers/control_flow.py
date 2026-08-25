"""Checker for rules triggered by control flow statements: IF, FOR, WHILE and their conditions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.api.parsing import Comment, EmptyLine, If
from robot.errors import VariableError

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

from robocop.linter.rules import VisitorChecker, misc
from robocop.linter.utils import misc as utils
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]
from robocop.version_handling import INLINE_IF_SUPPORTED

if TYPE_CHECKING:
    from robot.parsing.model import File, TestCase
    from robot.parsing.model.blocks import For, While
    from robot.parsing.model.statements import Error, KeywordCall, Node


class ControlFlowChecker(VisitorChecker):
    """
    Checker for rules reported for IF, FOR and WHILE blocks and the conditions used in them.

    The visitor keeps track of the loop nesting level and of blocks that failed to parse, and the rules decide
    whether the statement or the condition should be reported.
    """

    if_can_be_merged: misc.IfCanBeMergedRule
    inline_if_can_be_used: misc.InlineIfCanBeUsedRule
    multiline_inline_if: misc.MultilineInlineIfRule
    statement_outside_loop: misc.StatementOutsideLoopRule
    expression_can_be_simplified: misc.ExpressionCanBeSimplifiedRule
    misplaced_negative_condition: misc.MisplacedNegativeConditionRule
    not_enough_whitespace_around_operator: misc.NotEnoughWhitespaceAroundOperatorRule

    condition_keywords = frozenset(
        {
            "passexecutionif",
            "setvariableif",
            "shouldbetrue",
            "shouldnotbetrue",
            "skipif",
        }
    )

    def __init__(self) -> None:
        self.loops = 0
        self.skip_if_rules = False
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.loops = 0
        self.skip_if_rules = False
        self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.check_block_with_ifs(node)

    visit_Keyword = visit_TestCase  # noqa: N815

    def visit_If(self, node: If) -> None:  # noqa: N802
        condition_token = node.header.get_token(Token.ARGUMENT)
        self.check_condition(node.header.type, condition_token, node.condition)
        self.check_block_with_ifs(node)

    def visit_For(self, node: For) -> None:  # noqa: N802
        self.loops += 1
        self.check_block_with_ifs(node)
        self.loops -= 1

    def visit_While(self, node: While) -> None:  # noqa: N802
        condition_token = node.header.get_token(Token.ARGUMENT)
        self.check_condition(node.header.type, condition_token, node.condition)
        self.loops += 1
        # WHILE bodies were never scanned for adjacent IFs, only the IF blocks nested in them
        self.generic_visit(node)
        self.loops -= 1

    def check_block_with_ifs(self, node: Node) -> None:
        """
        Scan the body of a block for adjacent IF blocks and descend into it.

        The IF rules used to live in a visitor that stopped descending as soon as it met a block that failed to
        parse. Descending is now unconditional because the other rules need it, so the IF rules are skipped for
        the whole sub-tree with a flag instead.
        """
        skip = self.skip_if_rules or bool(node.errors)
        if not skip:
            self.check_adjacent_ifs(node)
        previous_skip, self.skip_if_rules = self.skip_if_rules, skip
        self.generic_visit(node)
        self.skip_if_rules = previous_skip

    def check_adjacent_ifs(self, node: Node) -> None:
        previous_if = None
        for child in node.body:
            if isinstance(child, If):
                if child.header.errors:
                    continue
                self.check_whether_if_should_be_inline(child)
                if previous_if and child.header:
                    self.if_can_be_merged.check(child, previous_if)
                previous_if = child
            elif not isinstance(child, (Comment, EmptyLine)):
                previous_if = None

    def check_whether_if_should_be_inline(self, node: If) -> None:
        if not INLINE_IF_SUPPORTED:
            return
        if isinstance(node.header, InlineIfHeader):
            self.multiline_inline_if.check(node)
            return
        self.inline_if_can_be_used.check(node)

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if not node.errors and not self.loops:
            self.statement_outside_loop.check_keyword(node)
        self.check_condition_keyword(node)

    def check_condition_keyword(self, node: KeywordCall) -> None:
        """Check conditions passed to BuiltIn keywords that evaluate an expression."""
        normalized_name = utils.normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name not in self.condition_keywords:
            return
        condition_token = node.get_token(Token.ARGUMENT)
        if not condition_token:
            return
        self.check_condition(node.keyword, condition_token, condition_token.value)
        if normalized_name == "setvariableif":
            arguments = node.get_tokens(Token.ARGUMENT)
            if len(arguments) < 4:
                return
            for argument in arguments[2::2]:
                self.check_condition(node.keyword, argument, argument.value)

    def check_condition(self, node_name: str, condition_token: Token, condition: str) -> None:
        if not condition:
            return
        self.not_enough_whitespace_around_operator.check(condition_token, node_name, condition)
        try:
            variables = list(VariableMatches(condition))
        except VariableError:  # for example ${variable which wasn't closed properly
            return
        position = condition_token.col_offset + 1
        for match in variables:
            position += len(match.before)
            self.misplaced_negative_condition.check(condition_token, node_name, match.before, match.match, match.after)
            self.expression_can_be_simplified.check(
                condition_token, node_name, match.before, match.match, match.after, position
            )

    def visit_Continue(self, node: Node) -> None:  # noqa: N802
        if not self.loops:
            self.statement_outside_loop.check_statement(node, "CONTINUE")

    def visit_Break(self, node: Node) -> None:  # noqa: N802
        if not self.loops:
            self.statement_outside_loop.check_statement(node, "BREAK")

    def visit_Error(self, node: Error) -> None:  # noqa: N802
        self.statement_outside_loop.check_error(node)
