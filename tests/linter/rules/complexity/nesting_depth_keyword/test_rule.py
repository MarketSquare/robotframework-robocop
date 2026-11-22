from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_max_depth(self):
        self.check_rule(
            configure=["nesting-depth-keyword.max_depth=2"],
            src_files=["test.robot"],
            expected_file="expected_output_max_depth.txt",
        )

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "nesting-depth-keyword.max_depth=3",
                "nesting-depth-keyword.severity_threshold=i=4:w=5:e=6",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )

    def test_resource_file(self):
        self.check_rule(src_files=["keywords.resource"], expected_file="expected_output_resource.txt")

    def test_tabs_and_mixed_separators(self):
        self.check_rule(
            configure=["nesting-depth-keyword.max_depth=3"],
            src_files=["tabs.robot"],
            expected_file="expected_output_tabs.txt",
        )

    def test_groups(self):
        self.check_rule(
            configure=["nesting-depth-keyword.max_depth=2"],
            src_files=["groups.robot"],
            expected_file="expected_output_groups.txt",
            test_on_version=">=7.2",
        )

    def test_disablers(self):
        self.check_rule(
            configure=["nesting-depth-keyword.max_depth=3"],
            src_files=["disablers.robot"],
            expected_file="expected_output_disablers.txt",
        )

    def test_invalid_syntax(self):
        self.check_rule(
            configure=["nesting-depth-keyword.max_depth=3"],
            src_files=["invalid.robot"],
            expected_file="expected_output_invalid.txt",
        )
