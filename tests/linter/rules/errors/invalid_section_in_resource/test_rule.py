from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt", target_version=">=6")

    def test_rule_pre6(self):
        self.check_rule(expected_file="expected_output_pre6.txt", target_version="<6")
