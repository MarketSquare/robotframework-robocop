from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=5.0")

    def test_severity_threshold(self):
        self.check_rule(
            config="-c inline-if-can-be-used:severity_threshold:warning=40",
            src_files=["severity.robot"],
            expected_file="expected_output_severity.txt",
            target_version=">=5.0",
        )
