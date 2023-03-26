from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt")

    def test_ignore_docs(self):
        self.check_rule(
            config="-c misaligned-continuation-row:ignore_docs:False",
            src_files=["test.robot"],
            expected_file="expected_output_ignore_docs.txt",
        )
