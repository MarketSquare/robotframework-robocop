from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["."], expected_file="expected_output.txt", issue_format="end_col", project_check=True
        )

    def test_extended(self):
        self.check_rule(
            src_files=["."], expected_file="expected_extended.txt", output_format="extended", project_check=True
        )
