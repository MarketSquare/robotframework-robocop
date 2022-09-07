from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_templated(self):
        self.check_rule(
            config="-c missing-doc-test-case:ignore_templated:False",
            src_files=["templated.robot"],
            expected_file="expected_output_templated.txt",
        )
