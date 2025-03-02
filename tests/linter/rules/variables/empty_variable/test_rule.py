from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=7")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7",
        )

    def test_rule_only_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_var.txt",
            configure=["empty-variable.variable_source=var"],
            test_on_version=">=7",
        )

    def test_rule_only_var_section(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_var.txt",
            configure=["empty-variable.variable_source=section"],
            test_on_version=">=7",
        )

    def test_rule_pre_var(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_var.txt", test_on_version="<7")
