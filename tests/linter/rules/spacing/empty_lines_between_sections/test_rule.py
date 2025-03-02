from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["golden.robot", "empty_section.robot", "test.robot", "one_section.robot", "bug861.robot"],
            expected_file="expected_output.txt",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["golden.robot", "empty_section.robot", "test.robot", "one_section.robot", "bug861.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )
