from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt", target_version=">=4")

    def test_rf3(self):
        self.check_rule(expected_file="expected_output_rf3.txt", target_version="==3.*")
