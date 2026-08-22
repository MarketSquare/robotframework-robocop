from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["__init__.robot", "test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(
            src_files=["__init__.robot", "test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )

    def test_test_case_metadata(self):
        """Test case metadata is scoped to the test case and can repeat suite or other test metadata."""
        self.check_rule(
            src_files=["test_case_metadata.robot"],
            expected_file="expected_output_test_case_metadata.txt",
            test_on_version=">=7.5",
        )
