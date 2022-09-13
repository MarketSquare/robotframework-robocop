from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "templated_test.robot", "templated_suite.robot"],
            expected_file="expected_output.txt",
        )

    def test_ignore_templated(self):
        self.check_rule(
            config="-c too-many-calls-in-test-case:ignore_templated:True",
            src_files=["ignore_templated"],
            expected_file="ignore_templated/expected_output.txt",
        )

    def test_severity(self):
        self.check_rule(
            config="-c too-many-calls-in-test-case:max_calls:5 -c too-many-calls-in-test-case:severity_threshold:warning=5:error=10",
            src_files=["severity"],
            expected_file="severity/expected_output.txt",
        )
