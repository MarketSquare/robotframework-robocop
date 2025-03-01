from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_severity_threshold(self):
        self.check_rule(
            configure=["line-too-long.severity_threshold=warning=100:info=50:error=150"],
            src_files=["severity_threshold.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )


# TODO: test with line length
