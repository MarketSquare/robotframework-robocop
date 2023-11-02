from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=4")

    def test_rule_rf3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", target_version="==3.*")

    def test_rule_on_loops(self):
        self.check_rule(
            src_files=["loops.robot"],
            expected_file="expected_output_loops.txt",
            issue_format="end_col",
            target_version=">=5",
        )

    def test_rule_inline_if(self):
        self.check_rule(src_files=["inline_if.robot"], expected_file=None, target_version=">=4")
