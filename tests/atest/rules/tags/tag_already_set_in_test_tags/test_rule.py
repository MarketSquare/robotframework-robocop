from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_test_tags(self):
        self.check_rule(
            src_files=["test_tags.robot"], expected_file="expected_output_test_tags.txt", target_version=">=6"
        )
