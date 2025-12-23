from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["multiline_force_tags.robot"],
            expected_file=None,
            test_on_version=">=6",
        )

    def test_rule_fix(self):
        self.check_rule_fix(
            source="multiline_force_tags.robot",
            expected="multiline_force_tags_fixed.robot",
            test_on_version=">=6",
            fix=True,
        )
