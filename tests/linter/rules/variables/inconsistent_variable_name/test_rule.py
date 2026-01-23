from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_with_var_type(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_rf7_3.txt",
            issue_format="end_col",
            test_on_version=">=7.3",
        )

    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output.txt",
            issue_format="end_col",
            test_on_version=">=7;<7.3",
        )

    def test_extended_with_var_type(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended_rf7_3.txt",
            output_format="extended",
            test_on_version=">=7.3",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7;<7.3",
        )

    def test_rule_pre_rf7(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_7.txt",
            issue_format="end_col",
            test_on_version="<7",
        )

    def test_var_syntax(self):
        self.check_rule(src_files=["VAR_syntax.robot"], expected_file=None, test_on_version=">=7")
