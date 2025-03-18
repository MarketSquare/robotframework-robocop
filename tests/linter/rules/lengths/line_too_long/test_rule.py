import textwrap

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_severity_threshold(self):
        self.check_rule(
            configure=["line-too-long.severity_threshold=warning=100:info=50:error=150"],
            src_files=["severity_threshold.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )

    def test_configure_invalid_line_length(self):
        self.check_rule(
            configure=["line-too-long.line_length=string"], expected_file="expected_exception.txt", exit_code=2
        )

    def test_configuring_non_existing_param(self):
        expected = textwrap.dedent(
            """
            ConfigurationError: Provided param 'unknown' for rule 'line-too-long' does not exist. Available configurables for this rule:
                severity = W
                    type: parser
                    info: Rule severity (E = Error, W = Warning, I = Info)
                severity_threshold
                line_length = 120
                    type: int
                    info: number of characters allowed in line
                ignore_pattern = re.compile('https?://\\\\S+')
                    type: pattern_type
                    info: ignore lines that contain configured pattern
            """  # noqa: E501
        ).lstrip()
        output = self.check_rule(
            src_files=["test.robot"], configure=["line-too-long.unknown=value"], exit_code=2, compare_output=False
        )
        assert output == expected

    def test_configure_invalid_rule_severity(self):
        expected = textwrap.dedent("""
        RuleParamFailedInitError: Failed to configure param `severity` with value `value`. Received error `Choose one from: I, W, E.`.
            Parameter type: <bound method RuleSeverity.parser of <enum 'RuleSeverity'>>
            Parameter info: Rule severity (E = Error, W = Warning, I = Info)
        """).lstrip()  # noqa: E501
        output = self.check_rule(
            src_files=["test.robot"], configure=["line-too-long.severity=value"], exit_code=2, compare_output=False
        )
        assert output == expected
