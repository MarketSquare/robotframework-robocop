from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["."], expected_file="expected_output.txt", project_check=True)

    def test_libraries_not_imported(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_output_not_imported.txt",
            analyze_libraries=False,
            project_check=True,
        )

    def test_ignored_library(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_output_not_imported.txt",
            ignored_library=["NotInstalled*"],
            project_check=True,
        )

    def test_extended(self):
        self.check_rule(
            src_files=["."],
            expected_file="expected_extended.txt",
            output_format="extended",
            project_check=True,
        )
