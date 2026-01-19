from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output.txt",
            test_on_version=">=5",
        )

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended", test_on_version=">=5")

    def test_fix(self):
        self.check_rule_fix(
            src_files=["test_fix.robot"],
            expected_dir="expected_fixed",
            test_on_version=">=5",
        )
