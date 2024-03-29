from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "test_lang.resource"], expected_file="expected_output.txt", target_version=">=6.1"
        )
