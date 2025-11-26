from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity


class CustomRule(Rule):
    @property
    def docs_url(self):
        return f"https://your.company.com/robocop/rules/{self.name}"


class ExternalRule(CustomRule):
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
