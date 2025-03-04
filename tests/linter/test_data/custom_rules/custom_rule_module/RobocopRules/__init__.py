from robocop.linter.rules import Rule, RuleSeverity

from .some_rules import CustomRuleChecker

rules = {
    "9903": Rule(
        rule_id="9903",
        name="external-rule",
        msg="This is external rule with {{ parameter }} in msg",
        severity=RuleSeverity.INFO,
    )
}
