from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output_rf7.txt", target_version=">=7")

    def test_rule_rf61(self):
        self.check_rule(expected_file="expected_output.txt", target_version="==6.1.*")

    def test_rule_rf6(self):
        self.check_rule(expected_file="expected_output_rf6.txt", target_version="==6.0")

    def test_rule_rf5(self):
        self.check_rule(expected_file="expected_output_rf5.txt", target_version="==5.*")

    def test_rule_rf4(self):
        self.check_rule(expected_file="expected_output_rf4.txt", target_version="==4.1.3")

    def test_rule_rf3(self):
        self.check_rule(expected_file="expected_output_rf3.txt", target_version="==3.2.2")
