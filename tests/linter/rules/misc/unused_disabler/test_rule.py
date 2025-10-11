from tests.linter.utils import RuleAcceptance

SELECT = [
    "unused-disabler",
    "multiline-inline-if",
    "duplicated-variable",
    "NAME01",
    "NAME02",
    "VAR02",
]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt", select=SELECT, test_on_version=">=5")

    def test_rule_rf4(self):
        self.check_rule(expected_file="expected_output_rf4.txt", select=SELECT, test_on_version="==4.*")

    def test_extended(self):
        self.check_rule(
            expected_file="expected_extended.txt", output_format="extended", select=SELECT, test_on_version=">=5"
        )
