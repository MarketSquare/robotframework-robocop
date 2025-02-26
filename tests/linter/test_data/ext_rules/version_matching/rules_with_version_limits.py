from robocop.linter.rules import VisitorChecker
from robocop.linter.rules import Rule, RuleSeverity

rules = {
    "1101": Rule(rule_id="1101", name="no-version", msg="No version", severity=RuleSeverity.INFO),
    "1102": Rule(rule_id="1102", name="lower-than-5", msg="Lower than", severity=RuleSeverity.INFO, version="<5"),
    "1103": Rule(
        rule_id="1103",
        name="higher-or-equal-than-5",
        msg="Higher or equal than",
        severity=RuleSeverity.INFO,
        version=">=5",
    ),
    "1104": Rule(
        rule_id="1104", name="range-5-and-6", msg="Version range", severity=RuleSeverity.INFO, version=">5;<=6"
    ),
}


class EmptyChecker(VisitorChecker):
    """Checker for keyword calls after [Return] statement."""

    reports = ("no-version", "lower-than-5", "higher-or-equal-than-5", "range-5-and-6")
