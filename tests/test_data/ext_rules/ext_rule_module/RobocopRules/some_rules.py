from robocop.checkers import VisitorChecker


class CustomRuleChecker(VisitorChecker):
    """Checker for missing keyword name."""

    reports = ("external-rule",)

    def visit_KeywordCall(self, node):  # noqa
        if node.keyword and "Dummy" not in node.keyword:
            self.report("external-rule", node=node)
