from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    rule_name = "missing-keyword-prefix"

    def test_rule(self):
        self.check_rule(src_files=["."], expected_file="expected_output.txt", project_check=True)

    def test_extended(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_extended.txt",
            output_format="extended",
            project_check=True,
        )

    def test_ignored_sources(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_ignored_sources.txt",
            configure=["missing-keyword-prefix.ignored_sources=BuiltIn,Collections,Str"],
            project_check=True,
        )
