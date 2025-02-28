from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt", test_on_version=">=6")

    def test_rule_pre6(self):
        self.check_rule(expected_file="expected_output_pre6.txt", test_on_version="<6")

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended")
