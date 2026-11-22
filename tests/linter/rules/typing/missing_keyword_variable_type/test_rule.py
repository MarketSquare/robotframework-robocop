from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "tasks.robot"],
            expected_file="expected_output.txt",
            test_on_version=">=7.3",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "tasks.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=7.3",
        )

    def test_assignment_ranges(self):
        self.check_rule(
            src_files=["assignment_ranges.robot"],
            expected_file="expected_assignment_ranges.txt",
            select=["missing-section-variable-type", "missing-keyword-variable-type", "missing-test-variable-type"],
            issue_format="end_col",
            test_on_version=">=7.3",
        )
