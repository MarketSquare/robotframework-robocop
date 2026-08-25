from tests.linter.utils import RuleAcceptance

SELECT = [
    "unused-disabler",
    "line-too-long",
    "multiline-inline-if",
    "duplicated-variable",
    "NAME01",
    "NAME18",
    "VAR02",
]
SRC_FILES = [
    "disabled_whole_no_violation.robot",
    "disabled_whole_rule.robot",
    "disabled_whole_with_violation.robot",
    "no_disablers.robot",
    "test.robot",
]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_output.txt", select=SELECT, test_on_version=">=5")

    def test_rule_rf4(self):
        self.check_rule(
            src_files=SRC_FILES, expected_file="expected_output_rf4.txt", select=SELECT, test_on_version="==4.*"
        )

    def test_extended(self):
        self.check_rule(
            src_files=SRC_FILES,
            expected_file="expected_extended.txt",
            output_format="extended",
            select=SELECT,
            test_on_version=">=5",
        )

    def test_fix(self):
        self.check_rule_fix(src_files=["fix_disablers.robot"], test_on_version=">=5")
