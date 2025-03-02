from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf5.txt", test_on_version=">=5")

    def test_rf_4(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", test_on_version="==4.*")

    def test_rf_3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", test_on_version="==3.*")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5",
        )
