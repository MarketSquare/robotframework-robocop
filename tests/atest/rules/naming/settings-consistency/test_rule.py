from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_rf6(self):
        self.check_rule(
            src_files=["task-with-test.robot", "test-with-task.robot", "golden-task.robot", "golden-test.robot"],
            expected_file="expected_output_rf6.txt",
            target_version="==6.*",
        )

    def test_rule(self):
        self.check_rule(
            src_files=["task-with-test.robot", "test-with-task.robot", "golden-task.robot", "golden-test.robot"],
            expected_file="expected_output_pre_rf6.txt",
            target_version="<6",
        )
