from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=5", issue_format="end_col"
        )

    def test_rule_rf3(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf3.txt", target_version="==3.*")

    def test_rule_rf4(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_rf4.txt", target_version="==4.*")

    def test_groups(self):
        self.check_rule(
            src_files=["groups.robot"],
            expected_file=None,
            target_version=">=7.2",
        )
