from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_max_depth(self):
        self.check_rule(
            configure=["nesting-depth-test-case.max_depth=1"],
            src_files=["test.robot"],
            expected_file="expected_output_max_depth.txt",
        )

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "nesting-depth-test-case.max_depth=2",
                "nesting-depth-test-case.severity_threshold=i=3:w=4:e=5",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )

    def test_tasks(self):
        self.check_rule(src_files=["tasks.robot"], expected_file="expected_output_tasks.txt")

    def test_group_and_templates(self):
        self.check_rule(
            src_files=["group_and_templates.robot"],
            expected_file="expected_output_group_and_templates.txt",
            test_on_version=">=7.2",
        )
