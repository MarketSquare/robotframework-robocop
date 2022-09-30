from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_rule_rf6(self):
        self.check_rule(expected_file="expected_output_rf6_0.txt", target_version=">=6.0")
