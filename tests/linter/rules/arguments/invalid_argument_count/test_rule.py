from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    rule_name = "invalid-argument-count"

    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_output.txt",
            exclude=["library"],
            project_check=True,
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_extended.txt",
            output_format="extended",
            exclude=["library"],
            project_check=True,
        )

    def test_library_keywords(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_output.txt",
            test_dir=self.test_class_dir / "library",
            project_check=True,
        )

    def test_libraries_are_not_analyzed_when_disabled(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_no_libraries.txt",
            test_dir=self.test_class_dir / "library",
            project_check=True,
            analyze_libraries=False,
        )
