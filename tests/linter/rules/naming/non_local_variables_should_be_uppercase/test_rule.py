from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_var(self):
        self.check_rule(src_files=["VAR_syntax.robot"], expected_file="expected_output_var.txt", target_version=">=7")
