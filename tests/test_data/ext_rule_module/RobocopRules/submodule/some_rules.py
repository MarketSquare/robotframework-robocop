from robocop.checkers import VisitorChecker
from robocop.rules import Rule

rules = {"9904": Rule(rule_id="9904", name="external-rule2", msg="This is external rule", severity="I")}


class CustomRuleChecker2(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule2",)

    def visit_KeywordCall(self, node):  # noqa
        if node.keyword and "Dummy" not in node.keyword:
            self.report("external-rule2", node=node)
