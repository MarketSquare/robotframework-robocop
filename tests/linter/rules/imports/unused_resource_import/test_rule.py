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
