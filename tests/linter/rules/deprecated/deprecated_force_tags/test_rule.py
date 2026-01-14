from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "test_tags.robot"], expected_file="expected_output.txt", test_on_version=">=6"
        )

    def test_rule_extended(self):
        self.check_rule(
            src_files=["test.robot", "test_tags.robot"],
            expected_file="expected_output_extended.txt",
            output_format="extended",
            test_on_version=">=6",
        )

    def test_fix(self):
        """Test that fixes are applied correctly."""
        self.check_rule_fix(src_files=["test.robot"], expected_dir="expected_fixed", test_on_version=">=6")

    def test_dif_mode(self):
        self.check_rule_fix(src_files=["test.robot"], expected_dir="expected_diff", diff=True, test_on_version=">=6")
