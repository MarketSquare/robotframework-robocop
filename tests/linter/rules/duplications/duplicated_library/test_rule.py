from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_rf6.txt", test_on_version="<6.0")

    def test_rule_rf6(self):
        self.check_rule(expected_file="expected_output_rf6.txt", test_on_version=">=6.0")
