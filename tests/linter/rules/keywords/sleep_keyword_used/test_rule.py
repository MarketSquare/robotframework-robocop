from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_rule_1s(self):
        self.check_rule(
            configure=["sleep-keyword-used.max_time=1s"],
            src_files=["test.robot"],
            expected_file="expected_output_1s.txt",
        )

    def test_rule_1min(self):
        self.check_rule(
            configure=["sleep-keyword-used.max_time=1min"],
            src_files=["test.robot"],
            expected_file="expected_output_1min.txt",
        )
