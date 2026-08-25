from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=7.2")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7.2",
        )

    def test_configure_min_calls(self):
        self.check_rule(
            configure=["too-few-calls-in-group.min_calls=1"],
            src_files=["test.robot"],
            expected_file=None,
            test_on_version=">=7.2",
        )
