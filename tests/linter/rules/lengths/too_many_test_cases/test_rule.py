from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot", "templated_test.robot"], expected_file="expected_output.txt")

    def test_severity(self):
        self.check_rule(
            config="-c too-many-test-cases:max_testcases:2 "
            "-c too-many-test-cases:max_templated_testcases:2 "
            "-c too-many-test-cases:severity_threshold:error=4",
            src_files=["severity"],
            expected_file="severity/expected_output.txt",
        )
