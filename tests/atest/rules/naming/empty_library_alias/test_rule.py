from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=5")

    def test_pre_rf5(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_rf5.txt", target_version="<5")
