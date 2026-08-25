from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_group(self):
        self.check_rule(src_files=["group.robot"], expected_file="expected_group.txt", test_on_version=">=7")

    def test_configure_allowed_empty_lines(self):
        self.check_rule(
            src_files=["test.robot"],
            configure=["empty-lines-inside-block.empty_lines=1"],
            expected_file="expected_configured.txt",
        )
