from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

rules = {
    "1102": Rule(
        rule_id="1102",
        name="smth2",
        msg="Keyword call after [Return] statement",
        severity=RuleSeverity.ERROR,
        enabled=False,
    )
}


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    reports = ("smth2",)

    def visit_Keyword(self, node):  # noqa: N802
        self.report("smth", node=node)
