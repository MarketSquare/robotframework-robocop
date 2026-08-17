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

    def test_disabled_by_default(self):
        assert not VariableInDocumentationRule.enabled
