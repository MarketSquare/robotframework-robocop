from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", issue_format="end_col")

    def test_extended(self):
        self.check_rule(src_files=["extended.robot"], expected_file="expected_extended.txt", output_format="extended")
