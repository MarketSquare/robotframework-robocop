from tests.linter.utils import RuleAcceptance

SRC_FILES = ["keyword_tags.robot", "no_tags_in_keywords.robot"]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_output.txt", test_on_version=">=6")

    def test_extended(self):
        self.check_rule(
            src_files=SRC_FILES,
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=6",
        )

    def test_fix(self):
        self.check_rule_fix(src_files=["fix_keyword_tags.robot"], test_on_version=">=6")
