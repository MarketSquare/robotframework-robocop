from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_pre(self):
        self.check_rule(
            src_files=["test.robot"], expected_file="expected_output.txt", issue_format="end_col", target_version=">=7"
        )

    def test_rule_pre_rf7(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_7.txt",
            issue_format="end_col",
            target_version="<7",
        )
