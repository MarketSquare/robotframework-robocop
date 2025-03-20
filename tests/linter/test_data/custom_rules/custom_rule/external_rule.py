from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity


class ExternalRule(Rule):
    name = "smth"
    rule_id = "EXT01"
    message = "Keyword call after [Return] statement"
    severity = RuleSeverity.ERROR



class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    smth: ExternalRule

    def visit_Keyword(self, node):  # noqa: N802
        self.report(self.smth, node=node)
