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

    def test_run_without_project_flag(self):
        """Project rules are run whenever they are enabled, even without the --project flag."""
        self.check_rule(src_files=["."], expected_file="expected_output.txt", issue_format="end_col")

    def test_no_project(self):
        self.check_rule(src_files=["."], expected_file=None, project=False, exit_code=0)
