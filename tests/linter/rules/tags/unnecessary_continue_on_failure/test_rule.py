from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    SRC_FILES = ["default_tags.robot", "local_tags.robot", "nested_blocks.robot"]

    def test_rule(self):
        self.check_rule(src_files=self.SRC_FILES, expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=self.SRC_FILES, expected_file="expected_extended.txt", output_format="extended")

    def test_test_tags(self):
        self.check_rule(
            src_files=["test_tags.robot"], expected_file="expected_output_test_tags.txt", test_on_version=">=6"
        )

    def test_keyword_tags(self):
        self.check_rule(
            src_files=["keyword_tags.robot"], expected_file="expected_output_keyword_tags.txt", test_on_version=">=6"
        )
