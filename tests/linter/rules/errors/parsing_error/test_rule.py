from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output_rf7_2.txt", test_on_version=">=7.2")

    def test_rule_rf7_1(self):
        self.check_rule(expected_file="expected_output_rf7_1.txt", test_on_version=">=7;<7.2")

    def test_rule_rf61(self):
        self.check_rule(expected_file="expected_output.txt", test_on_version="==6.1.*")

    def test_rule_rf6(self):
        self.check_rule(expected_file="expected_output_rf6.txt", test_on_version="==6.0")

    def test_rule_rf5(self):
        self.check_rule(expected_file="expected_output_rf5.txt", test_on_version="==5.*")

    def test_rule_rf4(self):
        self.check_rule(expected_file="expected_output_rf4.txt", test_on_version="==4.1.3")

    def test_rule_rf3(self):
        self.check_rule(expected_file="expected_output_rf3.txt", test_on_version="==3.2.2")

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended", test_on_version=">=7.2")
