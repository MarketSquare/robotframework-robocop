from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_before(self):
        self.check_rule(expected_file="expected_output_rf5.txt", target_version=">=5")

    def test_rule_before_rf5(self):
        self.check_rule(expected_file="expected_output.txt", target_version="<5")
