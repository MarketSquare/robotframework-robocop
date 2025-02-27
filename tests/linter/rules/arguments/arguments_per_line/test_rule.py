from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_rule_max_2(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_max_2.txt",
            configure=["arguments-per-line.max_args=2"],
        )
