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

    def test_no_cycle(self):
        self.check_rule(
            src_files=["."],
            expected_file=None,
            exit_code=0,
            project_check=True,
            test_dir=self.test_class_dir / "no_cycle",
        )
