from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_unrecognized_header_bug(self):
        self.check_rule(src_files=["unrecognized_header.robot"], expected_file=None)
