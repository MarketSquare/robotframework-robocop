from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["inline_if.robot", "invalid.robot", "test.robot"],
            expected_file="expected_output.txt",
            test_on_version=">=5.0",
        )

    def test_rule_rf4(self):
        self.check_rule(expected_file="expected_output_rf4.txt", test_on_version="==4.*")

    def test_extended(self):
        self.check_rule(
            src_files=["inline_if.robot", "invalid.robot", "test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5.0",
        )
