from tests.linter.utils import RuleAcceptance

SRC_FILES = [
    "bom_and_ignored_data.robot",
    "bom_and_two_ignored_lines.robot",
    "bom_example.robot",
    "just_ignored_rule.robot",
    "just_language_header.robot",
    "language_header_and_other.robot",
    "language_header_in_second_line.robot",
    "robotidy_disabler.robot",
    "test.robot",
    "with_ignored_data.robot",
    "with_ignored_rule_and_data.robot",
]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_extended.txt", output_format="extended")

    def test_fix(self):
        self.check_rule_fix(
            src_files=[
                "bom_and_two_ignored_lines.robot",
                "language_header_and_other.robot",
                "language_header_in_second_line.robot",
                "with_ignored_data.robot",
                "with_ignored_rule_and_data.robot",
            ]
        )
