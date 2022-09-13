from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_severity_threshold(self):
        self.check_rule(
            config="-c file-too-long:max_lines:300 -c file-too-long:severity_threshold:warning=300:error=400",
            src_files=["shorter.robot", "longer.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
