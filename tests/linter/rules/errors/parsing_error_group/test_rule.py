from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    rule_name = "parsing-error"

    def test_rule(self):
        self.check_rule(
            select=["parsing-error"],
            src_files=["groups.robot"],
            expected_file="expected_output.txt",
            test_on_version=">=7.2",
        )
