from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=7")

    def test_rule_only_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_var.txt",
            config="-c empty-variable:variable_source:var",
            target_version=">=7",
        )

    def test_rule_only_var_section(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_var.txt",
            config="-c empty-variable:variable_source:section",
            target_version=">=7",
        )

    def test_rule_pre_var(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_var.txt", target_version="<7")
