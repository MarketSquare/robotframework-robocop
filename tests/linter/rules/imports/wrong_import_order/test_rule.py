from tests.linter.utils import RuleAcceptance

SRC_FILES = [
    "no_builtins.robot",
    "no_imports.robot",
    "only_builtins.robot",
    "test.robot",
]


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=SRC_FILES, expected_file="expected_extended.txt", output_format="extended")

    def test_fix(self):
        self.check_rule_fix(src_files=["fix_imports.robot"])
