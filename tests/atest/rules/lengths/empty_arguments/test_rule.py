from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self, capsys):
        self.check_rule(capsys, src_files=["test.robot"], expected_file="expected_output.txt")
