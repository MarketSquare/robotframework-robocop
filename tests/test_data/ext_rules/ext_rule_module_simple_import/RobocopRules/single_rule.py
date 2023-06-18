from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity

rules = {
    "9903": Rule(
        rule_id="9903",
        name="external-rule",
        msg="This is external rule with {{ parameter }} in msg",
        severity=RuleSeverity.INFO,
    )
}


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule",)

    def visit_KeywordCall(self, node):  # noqa
        if node.keyword and "Dummy" not in node.keyword:
            self.report("external-rule", node=node)
