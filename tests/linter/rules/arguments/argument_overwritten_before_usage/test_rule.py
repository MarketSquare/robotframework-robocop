import textwrap

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_after_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_after_var.txt",
            issue_format="end_col",
            test_on_version=">=7",
        )

    def test_rule_pre_var(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre_var.txt",
            issue_format="end_col",
            test_on_version=">=5;<7",
        )

    def test_rule_rf3_rf4(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_rf3.txt",
            issue_format="end_col",
            test_on_version="<5",
        )

    def test_rule_arguments_should_clear_after_keyword(self):
        self.check_rule(src_files=["arguments_cleared_after_keyword.robot"], expected_file=None)

    def test_extended_view(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            test_on_version=">=7",
            output_format="extended",
        )

    def test_configuring_non_existing_param(self):
        expected = textwrap.dedent(
            """
            ConfigurationError: Provided param 'unknown' for rule 'argument-overwritten-before-usage' does not exist. Available configurable for this rule:
                severity = W
                    type: parser
                    info: Rule severity (E = Error, W = Warning, I = Info)
            """  # noqa: E501
        ).lstrip()
        output = self.check_rule(
            configure=["argument-overwritten-before-usage.unknown=value"], exit_code=2, compare_output=False
        )
        assert output == expected

    def test_variable_type_conversion(self):
        self.check_rule(
            src_files=["variable_type_conversion.robot"],
            expected_file="variable_type_conversion_expected.txt",
            # test_on_version=">=7.3" FIXME
        )
