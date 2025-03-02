from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["not_allowed_suite_foo.bar.robot", "suite.withdot"], expected_file="expected_output.txt"
        )

    def test_extended(self):
        self.check_rule(
            src_files=["not_allowed_suite_foo.bar.robot", "suite.withdot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )

    def test_configure_pattern(self):
        self.check_rule(
            configure=[r"not-allowed-char-in-filename.pattern=\.(?!bar)"],
            src_files=["allowed_suite_foo.bar.robot", "suite.withdot"],
            expected_file="expected_output_configured.txt",
        )
