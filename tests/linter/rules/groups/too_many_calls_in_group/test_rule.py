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

    def test_configure_max_calls(self):
        self.check_rule(
            configure=["too-many-calls-in-group.max_calls=100"],
            src_files=["test.robot"],
            expected_file=None,
            test_on_version=">=7.2",
        )
