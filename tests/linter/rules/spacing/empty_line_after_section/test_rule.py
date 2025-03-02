from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended")

    def test_severity(self):
        self.check_rule(
            configure=["empty-line-after-section.severity_threshold=error=2"],
            expected_file="expected_output_severity.txt",
        )
