from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(
            src_files=["__init__.robot", "__init__.resource", "test.robot"],
            expected_file="expected_output.txt",
            issue_format="end_col",
        )

    def test_pl_language(self):
        self.check_rule(
            src_files=["pl_language/__init__.robot", "pl_language/__init__.resource", "pl_language/test.robot"],
            expected_file="pl_language/expected_output.txt",
            issue_format="end_col",
            test_on_version=">=6",
        )

    def test_extended(self):
        self.check_rule(
            src_files=["__init__.robot", "__init__.resource", "test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )
