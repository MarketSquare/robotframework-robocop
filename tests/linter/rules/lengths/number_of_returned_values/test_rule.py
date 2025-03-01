from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=5.0")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5.0",
        )

    def test_rule_pre_rf5(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre_rf5.txt", test_on_version="<5.0")

    def test_severity_threshold(self):
        self.check_rule(
            configure=["number-of-returned-values.severity_threshold=error=6"],
            src_files=["severity.robot"],
            expected_file="expected_output_severity_threshold_rf5.txt",
            test_on_version=">=5.0",
        )

    def test_severity_threshold_pre_rf5(self):
        self.check_rule(
            configure=["number-of-returned-values.severity_threshold=error=6"],
            src_files=["severity.robot"],
            expected_file="expected_output_severity_threshold.txt",
            test_on_version="<5.0",
        )
