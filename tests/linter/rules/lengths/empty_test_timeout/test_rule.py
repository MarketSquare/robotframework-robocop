from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_explicit_none_is_not_reported(self):
        self.check_rule(src_files=["none_value.robot"], expected_file=None)

    def test_fix(self):
        self.check_rule_fix(src_files=["test.robot"])
