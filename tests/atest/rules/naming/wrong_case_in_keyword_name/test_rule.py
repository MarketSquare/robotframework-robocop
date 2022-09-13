from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot", "run_keywords.robot"], expected_file="expected_output.txt")

    def test_convention_first_word_capitalized(self):
        self.check_rule(
            config="-c wrong-case-in-keyword-name:convention:first_word_capitalized",
            src_files=["first_word"],
            expected_file="first_word/expected_output.txt",
        )

    def test_configure_pattern(self):
        self.check_rule(
            config="-c wrong-case-in-keyword-name:pattern:Foo\.bar",
            src_files=["configure_pattern"],
            expected_file="configure_pattern/expected_output.txt",
        )
