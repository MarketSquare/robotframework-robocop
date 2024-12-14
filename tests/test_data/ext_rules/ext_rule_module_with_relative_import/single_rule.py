from robocop.checkers import VisitorChecker
from robocop.rules import Rule, RuleSeverity
# Import starting with rules folder
from ext_rule_module_with_relative_import.bar import EXPECTED_KEYWORD

rules = {
    "9905": Rule(
        rule_id="9905",
        name="external-rule",
        msg="This is external rule with {{ parameter }} in msg",
        severity=RuleSeverity.INFO,
    )
}


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule",)

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and EXPECTED_KEYWORD not in node.keyword:
            self.report("external-rule", node=node)
