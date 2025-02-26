from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "templated_suite.robot"],
            expected_file="expected_output_rf6.txt",
            target_version=">=6",
        )

    def test_rule_rf5(self):
        self.check_rule(
            src_files=["test.robot", "templated_suite.robot"],
            expected_file="expected_output_rf5.txt",
            target_version="==5.*",
        )

    def test_pre_rf5(self):
        self.check_rule(src_files=["test.robot", "templated_suite.robot"], expected_file=None, target_version="<5.0")

    def test_force_tags(self):
        self.check_rule(
            src_files=["force_tags.robot"], expected_file="expected_output_force_tags.txt", target_version=">=6"
        )
