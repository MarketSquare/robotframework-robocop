from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=[">=7.0"])

    def test_pre_rf7(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output_pre7.txt", target_version="<7.0")
