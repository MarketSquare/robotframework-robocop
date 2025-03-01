from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_severity(self):
        self.check_rule(
            configure=["too-many-arguments.severity_threshold=warning=5:error=7"],
            src_files=["severity.robot"],
            expected_file="expected_output_severity.txt",
        )

    def test_disablers(self):
        self.check_rule(
            configure=["too-many-arguments.max_args=1"],
            src_files=["disablers.robot"],
            expected_file="expected_output_disablers.txt",
        )
