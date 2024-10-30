from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_builtin_syntax(self):
        self.check_rule(src_files=["test_builtin_syntax.robot"], expected_file="expected_output_builtin_syntax.txt")

    def test_rule_var_syntax(self):
        self.check_rule(
            src_files=["test_var_syntax.robot"], expected_file="expected_output_var_syntax.txt", target_version=">=7"
        )
