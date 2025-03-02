from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule_rf6(self):
        self.check_rule(
            src_files=[
                "tasks_with_test_settings.robot",
                "tests_with_task_settings.robot",
                "mixed_tasks.robot",
                "mixed_tests.robot",
                "golden_task.robot",
                "golden_test.robot",
                "__init__.robot",
            ],
            expected_file="expected_output_rf6.txt",
            test_on_version=">=6",
        )

    def test_rule(self):
        self.check_rule(
            src_files=[
                "tasks_with_test_settings.robot",
                "tests_with_task_settings.robot",
                "mixed_tasks.robot",
                "mixed_tests.robot",
                "golden_task.robot",
                "golden_test.robot",
                "__init__.robot",
            ],
            expected_file="expected_output_pre_rf6.txt",
            test_on_version="<6",
        )

    def test_extended(self):
        self.check_rule(
            src_files=[
                "tasks_with_test_settings.robot",
                "tests_with_task_settings.robot",
                "mixed_tasks.robot",
                "mixed_tests.robot",
                "golden_task.robot",
                "golden_test.robot",
                "__init__.robot",
            ],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=6",
        )
