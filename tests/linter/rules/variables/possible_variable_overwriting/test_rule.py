from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", test_on_version=">=7")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7",
        )

    def test_rule_pre_rf7(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre7.txt", test_on_version=">=6.1;<7")

    def test_pre_rf6_1(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output_pre6.1.txt",
            test_on_version=["==4.*", "==5.*", "==6.0"],
        )

    def test_rf3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", test_on_version="==3.*")

    def test_groups(self):
        self.check_rule(src_files=["groups.robot"], expected_file="expected_groups.txt", test_on_version=">=7.2")
