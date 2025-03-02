from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "test_lang.resource"], expected_file="expected_output.txt", test_on_version=">=6.1"
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "test_lang.resource"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=6.1",
        )
