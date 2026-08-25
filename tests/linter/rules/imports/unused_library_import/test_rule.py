from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["."], expected_file="expected_output.txt", project_check=True)

    def test_extended(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_extended.txt",
            output_format="extended",
            project_check=True,
        )

    def test_libraries_are_not_analyzed_when_disabled(self):
        self.check_rule(src_files=["."], expected_file=None, analyze_libraries=False, exit_code=0)

    def test_ignored_libraries_are_not_reported(self):
        self.check_rule(
            src_files=["."],
            expected_file=None,
            ignored_library=["OperatingSystem", "DateTime"],
            exit_code=0,
        )

    def test_library_keywords_with_embedded_arguments(self):
        self.check_rule(
            src_files=["."],
            expected_file=None,
            test_dir=self.test_class_dir / "embedded",
            project_check=True,
            exit_code=0,
        )
