from __future__ import annotations

from typing import TYPE_CHECKING

from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

if TYPE_CHECKING:
    from robot.parsing.model.blocks import Keyword, TestCase

rules = {
    "1101": Rule(rule_id="1101", name="not-deprecated", msg="Not deprecated", severity=RuleSeverity.ERROR),
    "1102": Rule(rule_id="1102", name="deprecated", msg="Deprecated", deprecated=True, severity=RuleSeverity.ERROR),
    "1103": Rule(
        rule_id="1103",
        name="deprecated-no-implementation",
        msg="Deprecated and without implementation",
        deprecated=True,
        severity=RuleSeverity.WARNING,
    ),
}


class FirstChecker(VisitorChecker):
    reports = ("not-deprecated", "deprecated")

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.report("not-deprecated", node=node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.report("deprecated", node=node)
