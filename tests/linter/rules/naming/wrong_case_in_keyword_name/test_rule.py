from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "templated_suite.robot", "run_keywords.robot"], expected_file="expected_output.txt"
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "templated_suite.robot", "run_keywords.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )

    def test_rule_pabot(self):
        self.check_rule(src_files=["pabot_run_keywords.robot"], expected_file="expected_output_pabot.txt")

    def test_convention_first_word_capitalized(self):
        self.check_rule(
            configure=["wrong-case-in-keyword-name.convention=first_word_capitalized"],
            src_files=["first_word"],
            expected_file="first_word/expected_output.txt",
        )

    def test_configure_pattern(self):
        self.check_rule(
            configure=[r"wrong-case-in-keyword-name.pattern=Foo\.bar"],
            src_files=["configure_pattern"],
            expected_file="configure_pattern/expected_output.txt",
        )
