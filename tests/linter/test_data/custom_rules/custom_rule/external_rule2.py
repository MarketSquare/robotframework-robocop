from robot.parsing.model.blocks import Keyword

from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity



class ExternalRule(Rule):
    name = "smth2"
    rule_id = "EXT02"
    message = "Keyword call after [Return] statement"
    severity = RuleSeverity.ERROR


class SmthChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    smth2: ExternalRule

    def visit_Keyword(self, node: Keyword) -> Keyword:  # noqa: N802
        self.report(self.smth2, node=node)
