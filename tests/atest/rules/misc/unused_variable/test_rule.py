from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", issue_format="end_col")

    def test_rule_on_loops(self):
        self.check_rule(
            src_files=["loops.robot"],
            expected_file="expected_output_loops.txt",
            issue_format="end_col",
            target_version=">=5",
        )
