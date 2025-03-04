from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

rules = {
    "1101": Rule(rule_id="1101", name="not-deprecated", msg="Not deprecated", severity=RuleSeverity.ERROR),
    "1102": Rule(rule_id="1102", name="deprecated", msg="Deprecated", deprecated=True, severity=RuleSeverity.ERROR),
    "1103": Rule(
        rule_id="1103",
        name="deprecated-no-implementation",
        msg="Deprecated and without implementation",
        deprecated=True,
        severity=RuleSeverity.WARNING,
    ),
}


class FirstChecker(VisitorChecker):
    reports = ("not-deprecated", "deprecated")

    def visit_Keyword(self, node):  # noqa: N802
        self.report("not-deprecated", node=node)

    def visit_TestCase(self, node):  # noqa: N802
        self.report("deprecated", node=node)
