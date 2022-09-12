from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_rule_rf5_1(self):
        self.check_rule(expected_file="expected_output_rf5_1.txt", target_version="==5.1")
