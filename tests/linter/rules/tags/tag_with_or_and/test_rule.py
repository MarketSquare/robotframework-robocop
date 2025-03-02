from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_keyword_tags(self):
        self.check_rule(
            src_files=["keyword_tags.robot"], expected_file="expected_output_keyword_tags.txt", test_on_version=">=6"
        )

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")
