from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf7_3.txt", test_on_version=">=7.3")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended_rf7_3.txt",
            output_format="extended",
            test_on_version=">=7.3",
        )

    def test_rule_before_typing(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version="<7.3")

    def test_extende_before_typingd(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version="<7.3",
        )
