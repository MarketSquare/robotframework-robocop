from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_after_var(self):
        self.check_rule(
            src_files=["test.robot", "unused_section_vars.robot"],
            expected_file="expected_output_after_var.txt",
            issue_format="end_col",
            test_on_version=">=7",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "unused_section_vars.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7",
        )

    def test_rule_pre_var(self):
        self.check_rule(
            src_files=["test.robot", "unused_section_vars.robot"],
            expected_file="expected_output_pre_var.txt",
            issue_format="end_col",
            test_on_version=">=4;<7",
        )

    def test_rule_on_loops(self):
        self.check_rule(
            src_files=["loops.robot"],
            expected_file="expected_output_loops.txt",
            issue_format="end_col",
            test_on_version=">=5",
        )

    def test_groups(self):
        self.check_rule(src_files=["groups.robot"], expected_file="expected_output_groups.txt", test_on_version=">=7.2")

    def test_extended_variable_syntax(self):
        self.check_rule(
            src_files=["extended_variable_syntax.robot"],
            expected_file=None,
        )
