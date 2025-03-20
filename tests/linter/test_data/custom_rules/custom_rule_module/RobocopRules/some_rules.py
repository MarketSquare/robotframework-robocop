from robocop.linter.rules import VisitorChecker, Rule, RuleSeverity


class ExternalRule(Rule):
    name = "external-rule"
    rule_id = "EXT03"
    message = "This is external rule with {parameter} in msg"
    severity = RuleSeverity.INFO


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    external_rule: ExternalRule

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and "Example" not in node.keyword:
            self.report(self.external_rule, node=node)
