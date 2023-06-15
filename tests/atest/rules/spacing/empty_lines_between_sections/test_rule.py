from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["golden.robot", "empty_section.robot", "test.robot", "one_section.robot"],
            expected_file="expected_output.txt",
        )
