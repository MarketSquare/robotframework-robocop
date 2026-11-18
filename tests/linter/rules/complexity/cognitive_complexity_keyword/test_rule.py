from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_info_warning_error_thresholds(self):
        self.check_rule(
            configure=[
                "cognitive-complexity-keyword.max_complexity=11",
                "cognitive-complexity-keyword.severity_threshold=e=19:i=11:w=15",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )

    def test_resource_file(self):
        self.check_rule(
            configure=["cognitive-complexity-keyword.max_complexity=10"],
            src_files=["keywords.resource"],
            expected_file="expected_output_resource.txt",
        )

    def test_rule_specific_disabler_keeps_other_rule(self):
        self.check_rule(
            select=["cognitive-complexity-keyword", "cyclomatic-complexity-keyword"],
            src_files=["disablers.robot"],
            expected_file="expected_output_disablers.txt",
        )

    def test_invalid_syntax(self):
        self.check_rule(src_files=["invalid.robot"], expected_file="expected_output_invalid.txt")
