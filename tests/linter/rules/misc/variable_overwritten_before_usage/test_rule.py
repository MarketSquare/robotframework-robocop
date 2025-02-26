from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_after_var(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_after_var.txt", target_version=">=7")

    def test_rule_pre_var(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_var.txt", target_version=">=4;<7")

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
