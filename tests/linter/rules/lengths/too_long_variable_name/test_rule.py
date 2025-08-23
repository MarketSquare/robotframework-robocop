from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )

    def test_severity_threshold(self):
        self.check_rule(
            configure=[
                "too-long-variable-name.severity_threshold=warning=20:error=40",
                "too-long-variable-name.max_len=20",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
