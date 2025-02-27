from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_configured_block(self):
        self.check_rule(
            configure=["missing-space-after-comment.block=^#[*]+"],
            src_files=["block.robot"],
            expected_file="expected_output_block.txt",
        )
