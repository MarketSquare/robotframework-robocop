from wrapper import errors
from robocop.linter.rules import Rule, RuleSeverity, VisitorChecker



class CustomRule(Rule):  # TODO docs
    name = "custom-rule"
    rule_id = "CUS01"
    message = "Message"
    severity = RuleSeverity.ERROR
    added_in_version = "1.0.0"


class CustomChecker(VisitorChecker):
    custom_rule: CustomRule

    def __init__(self):
        super().__init__()
