from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_before(self):
        self.check_rule(expected_file="expected_output.txt")
