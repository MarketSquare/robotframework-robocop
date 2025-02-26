from robocop.linter.rules import VisitorChecker


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule",)

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.keyword and "Example" not in node.keyword:
            self.report("external-rule", node=node)
