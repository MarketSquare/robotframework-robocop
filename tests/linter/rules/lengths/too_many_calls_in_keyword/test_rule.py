from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_severity(self):
        self.check_rule(
            config="-c too-many-calls-in-keyword:max_calls:5 "
            "-c too-many-calls-in-keyword:severity_threshold:warning=5:error=10",
            src_files=["severity.robot"],
            expected_file="expected_output_severity.txt",
        )
