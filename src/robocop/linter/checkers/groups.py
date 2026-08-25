"""Checker for rules triggered by the ``GROUP`` syntax."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker, groups
from robocop.linter.rules.lengths import count_keyword_calls

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.blocks import Group


class GroupChecker(VisitorChecker):
    """Checker for rules reported for ``GROUP`` blocks."""

    too_few_calls_in_group: groups.TooFewCallsInGroupRule
    too_many_calls_in_group: groups.TooManyCallsInGroupRule
    group_without_name: groups.GroupWithoutNameRule
    nested_group: groups.NestedGroupRule
    group_not_allowed: groups.GroupNotAllowedRule

    def __init__(self) -> None:
        self.group_depth = 0
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.group_depth = 0
        self.generic_visit(node)

    def visit_Group(self, node: Group) -> None:  # noqa: N802
        self.group_not_allowed.check(node)
        # Empty and unterminated groups are Robot Framework syntax errors reported by the parsing-error rule.
        if not node.errors:
            self.nested_group.check(node, self.group_depth)
            self.group_without_name.check(node)
            keyword_count = count_keyword_calls(node)
            if not self.too_many_calls_in_group.check(node, keyword_count):
                self.too_few_calls_in_group.check(node, keyword_count)
        self.group_depth += 1
        self.generic_visit(node)
        self.group_depth -= 1
