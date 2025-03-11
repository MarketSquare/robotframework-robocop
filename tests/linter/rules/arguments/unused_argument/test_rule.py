from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=5", issue_format="end_col"
        )

    def test_rule_rf3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", test_on_version="==3.*")

    def test_rule_rf4(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", test_on_version="==4.*")

    def test_groups(self):
        self.check_rule(
            src_files=["groups.robot"],
            expected_file=None,
            test_on_version=">=7.2",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            test_on_version=">=5",
            output_format="extended",
        )

    def test_extended_variable_syntax(self):
        self.check_rule(
            src_files=["extended_variable_syntax.robot"],
            expected_file=None,
        )
