from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf5.txt", target_version=">=5")

    def test_rf_4(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", target_version="==4.*")

    def test_rf_3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", target_version="==3.*")
