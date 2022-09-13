from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_keyword_doc(self):
        self.check_rule(src_files=["keyword_doc.robot"], expected_file="expected_output_keyword_doc.txt")
