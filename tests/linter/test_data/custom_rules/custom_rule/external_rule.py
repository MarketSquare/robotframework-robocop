from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity


class ExternalRule(Rule):
    """
    Keyword call after ``[Return]`` statement.

    ``[Return]`` setting does not return from keyword and only set which variables will be returned.
    To avoid confusion it is better to define it at the end of keyword.
    """
    name = "smth"
    rule_id = "EXT01"
    message = "Keyword call after [Return] statement"
    severity = RuleSeverity.ERROR



class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    smth: ExternalRule

    def visit_Keyword(self, node):  # noqa: N802
        self.report(self.smth, node=node)
