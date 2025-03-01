from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version="<7.2")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_with_groups(self):
        self.check_rule(src_files=["groups.robot"], expected_file="expected_output_groups.txt", test_on_version=">=7.2")

    def test_severity(self):
        self.check_rule(
            configure=[
                "too-many-calls-in-keyword.max_calls=5",
                "too-many-calls-in-keyword.severity_threshold=warning=5:error=10",
            ],
            src_files=["severity.robot"],
            expected_file="expected_output_severity.txt",
        )
