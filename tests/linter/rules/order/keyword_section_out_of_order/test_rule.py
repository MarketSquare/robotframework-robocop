from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_rule_setup(self):
        self.check_rule(
            src_files=["test.robot", "test_kw_setup_added_in_rf7.robot"],
            expected_file="expected_output_rf7.txt",
            test_on_version=">=7",
        )

    def test_rule_teardown_keyword(self):
        self.check_rule(
            src_files=["test.robot"],
            configure=["keyword-section-out-of-order.sections_order=teardown,keyword"],
            expected_file="expected_output_teardown_keyword.txt",
        )
