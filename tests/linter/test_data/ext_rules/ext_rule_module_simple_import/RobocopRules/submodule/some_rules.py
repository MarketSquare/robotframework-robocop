from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

rules = {"9904": Rule(rule_id="9904", name="external-rule2", msg="This is external rule", severity=RuleSeverity.INFO)}


class CustomRuleChecker2(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule2",)

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and "Example" not in node.keyword:
            self.report("external-rule2", node=node)
