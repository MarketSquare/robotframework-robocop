from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=7.0")

    def test_rf6(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre7.txt", test_on_version=">=6;<7")

    def test_rf4_rf5(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", test_on_version="<6")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7.0",
        )
