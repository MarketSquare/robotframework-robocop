from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(expected_file="expected_output.txt")

    def test_rule_teardown_keyword(self):
        self.check_rule(
            config="-c test-case-section-out-of-order:sections_order:teardown,keyword",
            expected_file="expected_output_teardown_keyword.txt",
        )
