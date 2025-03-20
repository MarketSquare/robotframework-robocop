from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker
# Import starting with rules folder
from custom_rule_module_with_relative_import.bar import EXPECTED_KEYWORD



class ExternalRule(Rule):
    name = "external-rule"
    rule_id = "EXT05"
    message = "This is external rule with {parameter} in msg"
    severity = RuleSeverity.ERROR


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    external_rule: ExternalRule

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and EXPECTED_KEYWORD not in node.keyword:
            self.report(self.external_rule, node=node)
