from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_configured_block(self):
        self.check_rule(
            config="-c missing-space-after-comment:block:^#[*]+",
            src_files=["block.robot"],
            expected_file="expected_output_block.txt",
        )
