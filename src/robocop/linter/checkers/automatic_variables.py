"""Checker for automatic variables with context-dependent availability."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter.rules import VisitorChecker, variables
from robocop.linter.utils import misc as utils
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import Node, Statement
    from robot.variables.search import VariableMatch


class AutomaticVariablesChecker(VisitorChecker):
    """Check automatic variable references in contexts known without resolving keyword calls."""

    automatic_variable_not_available: variables.AutomaticVariableNotAvailableRule

    def __init__(self) -> None:
        self.execution_context = "suite context"
        super().__init__()

    def visit_File(self, node: Node) -> None:  # noqa: N802
        self.execution_context = "suite context"
        self.generic_visit(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802, ARG002
        # The caller determines which automatic variables are available in a user keyword.
        return

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.visit_in_context(node, "test case body")

    def visit_Setup(self, node: Node) -> None:  # noqa: N802
        self.check_in_context(node, "test setup")

    visit_TestSetup = visit_Setup  # noqa: N815

    def visit_Teardown(self, node: Node) -> None:  # noqa: N802
        self.check_in_context(node, "test teardown")

    visit_TestTeardown = visit_Teardown  # noqa: N815

    def visit_SuiteSetup(self, node: Node) -> None:  # noqa: N802
        self.check_in_context(node, "suite setup")

    def visit_SuiteTeardown(self, node: Node) -> None:  # noqa: N802
        self.check_in_context(node, "suite teardown")

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        self.check_statement(node)

    def visit_in_context(self, node: Node, context: str) -> None:
        previous_context = self.execution_context
        self.execution_context = context
        self.generic_visit(node)
        self.execution_context = previous_context

    def check_in_context(self, node: Node, context: str) -> None:
        previous_context = self.execution_context
        self.execution_context = context
        self.check_statement(node)
        self.execution_context = previous_context

    def check_statement(self, node: Node) -> None:
        for token in node.data_tokens:
            if token.type in (Token.ASSIGN, Token.VARIABLE):
                continue
            for variable_match, offset in self.iter_variable_matches(token.value):
                normalized_name = utils.normalize_robot_name(variable_match.base)
                variable = f"{variable_match.identifier}{{{variable_match.base}}}"
                self.automatic_variable_not_available.check(
                    token=token,
                    variable=variable,
                    normalized_name=normalized_name,
                    context=self.execution_context,
                    offset=offset,
                )

    @classmethod
    def iter_variable_matches(cls, value: str, offset: int = 0) -> Iterator[tuple[VariableMatch, int]]:
        """Yield top-level and nested variable matches with offsets in the original token."""
        consumed = 0
        for variable_match in VariableMatches(value, ignore_errors=True):
            match_offset = offset + consumed + variable_match.start
            yield variable_match, match_offset
            yield from cls.iter_variable_matches(variable_match.base, match_offset + 2)
            item_start = len(variable_match.identifier) + len(variable_match.base) + 2
            for item in variable_match.items:
                item_start = variable_match.match.find(item, item_start)
                if item_start == -1:
                    continue
                yield from cls.iter_variable_matches(item, match_offset + item_start)
                item_start += len(item)
            consumed += variable_match.end
