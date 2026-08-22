from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_rule_teardown_keyword(self):
        self.check_rule(
            src_files=["test.robot"],
            configure=["test-case-section-out-of-order.sections_order=teardown,keyword"],
            expected_file="expected_output_teardown_keyword.txt",
        )

    def test_metadata(self):
        self.check_rule(
            src_files=["test_metadata.robot"],
            expected_file="expected_output_metadata.txt",
            test_on_version=">=7.5",
        )
