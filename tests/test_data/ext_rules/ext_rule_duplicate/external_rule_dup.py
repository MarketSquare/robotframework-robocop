from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

rules = {
    "1105": Rule(rule_id="1105", name="smth", msg="Keyword call after [Return] statement", severity=RuleSeverity.ERROR)
}


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    reports = ("smth",)

    def visit_Keyword(self, node):  # noqa
        self.report("smth", node=node)
