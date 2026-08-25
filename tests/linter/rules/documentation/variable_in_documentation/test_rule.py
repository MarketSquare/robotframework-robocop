from robocop.linter.rules.documentation import VariableInDocumentationRule
from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_on_all_supported_versions(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=5")

    def test_extended(self):
        self.check_rule(
            src_files=["extended.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5",
        )

    def test_split_variables_with_legacy_joining(self):
        self.check_rule(
            src_files=["split.robot"],
            expected_file="expected_split_legacy.txt",
            issue_format="end_col",
            test_on_version="<6.1",
        )

    def test_split_variables_with_modern_joining(self):
        self.check_rule(
            src_files=["split.robot"],
            expected_file="expected_split.txt",
            issue_format="end_col",
            test_on_version=">=6.1",
        )

    def test_disabled_and_not_fixable(self):
        assert not VariableInDocumentationRule.enabled
        assert not VariableInDocumentationRule.fixable
