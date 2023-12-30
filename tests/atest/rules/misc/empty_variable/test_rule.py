from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=7")

    def test_rule_pre_var(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_var.txt", target_version="<7")
