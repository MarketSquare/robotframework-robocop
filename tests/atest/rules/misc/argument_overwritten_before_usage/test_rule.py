from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"], expected_file="expected_output.txt", issue_format="end_col", target_version=">=5"
        )

    def test_rule_rf3_rf4(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_rf3.txt",
            issue_format="end_col",
            target_version="<5",
        )

    def test_rule_arguments_should_clear_after_keyword(self):
        self.check_rule(src_files=["arguments_cleared_after_keyword.robot"], expected_file=None)
