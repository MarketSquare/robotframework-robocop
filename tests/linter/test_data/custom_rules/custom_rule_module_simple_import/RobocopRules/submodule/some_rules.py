from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity


class ExternalRule(Rule):
    name = "external-rule"
    rule_id = "EXT04"
    message = "This is external rule"
    severity = RuleSeverity.INFO


class CustomRuleChecker2(VisitorChecker):
    """Checker for missing keyword name."""

    external_rule2: ExternalRule

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and "Example" not in node.keyword:
            self.report(self.external_rule2, node=node)
