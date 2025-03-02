from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output_rf5.txt", test_on_version=">=5")

    def test_rf4(self):
        self.check_rule(expected_file="expected_output_rf4.txt", test_on_version="==4.*")

    def test_rf3(self):
        self.check_rule(expected_file="expected_output_rf3.txt", test_on_version="==3.*")

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended", test_on_version=">=5")
