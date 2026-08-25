from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    rule_name = "missing-keyword-prefix"

    def test_rule(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_output.txt",
            exclude=["alias"],
            project_check=True,
        )

    def test_extended(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_extended.txt",
            output_format="extended",
            exclude=["alias"],
            project_check=True,
        )

    def test_ignored_sources(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_ignored_sources.txt",
            configure=["missing-keyword-prefix.ignored_sources=BuiltIn,Collections"],
            exclude=["alias"],
            project_check=True,
        )

    def test_library_alias(self):
        """Library imported with the ``AS`` syntax should be called using the alias."""
        self.check_rule(
            src_files=["."],
            expected_file="expected_output.txt",
            test_dir=self.test_class_dir / "alias",
            test_on_version=">=6",
            project_check=True,
        )
