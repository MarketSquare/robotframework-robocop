from .some_rules import CustomRuleChecker
from robocop.rules import Rule, RuleSeverity

rules = {"9903": Rule(rule_id="9903", name="external-rule", msg="This is external rule", severity=RuleSeverity.INFO)}
