from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "cyclomatic-complexity-keyword.max_complexity=9",
                "cyclomatic-complexity-keyword.severity_threshold=info=9:warning=11:error=12",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
