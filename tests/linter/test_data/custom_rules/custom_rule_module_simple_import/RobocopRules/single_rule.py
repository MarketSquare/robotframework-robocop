from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

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

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and "Example" not in node.keyword:
            self.report("external-rule", node=node)
