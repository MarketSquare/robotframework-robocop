from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt")

    def test_severity_threshold(self):
        self.check_rule(
            config="-c consecutive-empty-lines:severity_threshold:error=3",
            src_files=["test.robot", "golden_test.robot"],
            expected_file="expected_output_severity.txt",
        )
