from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["task-with-test.robot", "golden-task.robot", "golden-test.robot"],
            expected_file="expected_output.txt",
        )
