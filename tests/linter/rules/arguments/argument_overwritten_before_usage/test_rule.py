from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_after_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_after_var.txt",
            issue_format="end_col",
            test_on_version=">=7",
        )

    def test_rule_pre_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_var.txt",
            issue_format="end_col",
            test_on_version=">=5;<7",
        )

    def test_rule_rf3_rf4(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_rf3.txt",
            issue_format="end_col",
            test_on_version="<5",
        )

    def test_rule_arguments_should_clear_after_keyword(self):
        self.check_rule(src_files=["arguments_cleared_after_keyword.robot"], expected_file=None)

    def test_extended_view(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            test_on_version=">=7",
            output_format="extended",
        )
