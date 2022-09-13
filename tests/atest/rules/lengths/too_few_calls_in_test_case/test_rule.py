from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "templated_test.robot", "templated_suite.robot"],
            expected_file="expected_output.txt",
        )

    def test_templated(self):
        self.check_rule(
            config="-c too-few-calls-in-test-case:ignore_templated:True",
            src_files=["templated"],
            expected_file="templated/expected_output.txt",
        )

    def test_bug629(self):
        self.check_rule(
            config="-c too-few-calls-in-test-case:min_calls:2",
            src_files=["bug629/test.robot"],
            expected_file="bug629/expected_output.txt",
        )
