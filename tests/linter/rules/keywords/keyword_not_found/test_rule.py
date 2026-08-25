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

    def test_not_reported_without_library_analysis(self):
        self.check_rule(src_files=["."], expected_file=None, analyze_libraries=False, exit_code=0)

    def test_not_reported_when_library_is_ignored(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file=None,
            ignored_library=["Collections"],
            exit_code=0,
            project_check=True,
        )
