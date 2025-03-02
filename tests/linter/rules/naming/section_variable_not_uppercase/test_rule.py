from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=4")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=4",
        )

    def test_rule_rf3(self):
        # RF3 doesn't recognize nested variables in Variables section
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", test_on_version="==3.*")
