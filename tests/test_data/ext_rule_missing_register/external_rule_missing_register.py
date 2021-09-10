from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    rules = {"1101": ("smth", "Keyword call after [Return] statement", RuleSeverity.ERROR)}

    def visit_Keyword(self, node):  # noqa
        self.report("smth", node=node)
