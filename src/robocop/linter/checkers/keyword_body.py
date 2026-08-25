"""Checker for rules triggered by scanning the body of a keyword or a block."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker, misc

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Block
    from robot.parsing.model.statements import Node


class BodyChecker(VisitorChecker):
    """Checker for rules that scan the direct children of a keyword or a block."""

    keyword_after_return: misc.KeywordAfterReturnRule
    empty_return: misc.EmptyReturnRule
    unreachable_code: misc.UnreachableCodeRule
    nested_for_loop: misc.NestedForLoopRule

    def visit_Keyword(self, node: Block) -> None:  # noqa: N802
        self.keyword_after_return.check(node)
        self.empty_return.check(node)
        self.unreachable_code.check(node)
        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword  # noqa: N815

    def visit_ForLoop(self, node: Node) -> None:  # noqa: N802
        # For RF 4.0 node is "For" but we purposely don't visit it because nested for loop is allowed in 4.0
        self.nested_for_loop.check(node)
