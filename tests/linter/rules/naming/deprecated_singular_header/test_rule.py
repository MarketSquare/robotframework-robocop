from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt", target_version=">=6.0")

    def test_language(self):
        self.check_rule(
            config="--language pl", src_files=["language.robot"], expected_file=None, target_version=">=6.0"
        )

    def test_pre_rf5(self):
        self.check_rule(src_files=["test.robot"], expected_file=None, target_version="<5.0")
