from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf5.1.txt", target_version=">=5.1")

    def test_pre_rf5_1(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_rf5.1.txt", target_version="<5.1")
