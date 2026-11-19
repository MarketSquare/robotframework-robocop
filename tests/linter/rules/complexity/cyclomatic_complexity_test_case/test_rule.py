from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "cyclomatic-complexity-test-case.max_complexity=0",
                "cyclomatic-complexity-test-case.severity_threshold=info=1:warning=8:error=11",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
