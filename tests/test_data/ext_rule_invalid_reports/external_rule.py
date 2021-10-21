from robocop.checkers import VisitorChecker
from robocop.rules import Rule

rules = {"1101": Rule(rule_id="1101", name="smth", msg="Keyword call after [Return] statement", severity="E")}


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    reports = ("idontexist",)

    def visit_Keyword(self, node):  # noqa
        self.report("smth", node=node)
