from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf6_0.txt", test_on_version=">=6.0")

    def test_pre_rf6(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_rf6_0.txt", test_on_version="<6.0")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=6.0",
        )
