from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt")

    def test_severity(self):
        self.check_rule(
            config="-c empty-line-after-section:severity_threshold:error=2",
            expected_file="expected_output_severity.txt",
        )
