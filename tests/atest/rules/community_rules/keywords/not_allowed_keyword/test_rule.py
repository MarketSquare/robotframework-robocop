from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_output.txt",
            config="-c not-allowed-keyword:keywords:NotAllowed,Not_AllowedWithArgs,library.not_allowed_with_lib",
            issue_format="end_col",
        )
