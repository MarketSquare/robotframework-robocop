from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "cognitive-complexity-test-case.max_complexity=9",
                "cognitive-complexity-test-case.severity_threshold=info=9:warning=12:error=21",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )

    def test_tasks(self):
        self.check_rule(src_files=["tasks.robot"], expected_file="expected_output_tasks.txt")

    def test_group_and_var(self):
        self.check_rule(
            src_files=["group_and_var.robot"],
            expected_file="expected_output_group_and_var.txt",
            test_on_version=">=7.2",
        )
