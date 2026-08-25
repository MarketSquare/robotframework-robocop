from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    rule_name = "missing-argument-name"

    def test_rule(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_output.txt",
            project_check=True,
        )

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_extended.txt",
            output_format="extended",
            project_check=True,
        )

    def test_min_arguments(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_min_arguments.txt",
            configure=["missing-argument-name.min_arguments=2"],
            project_check=True,
        )

    def test_library_keywords(self):
        self.check_rule(
            src_files=["test.robot", "keywords.resource"],
            expected_file="expected_library_keywords.txt",
            configure=["missing-argument-name.ignore_library_keywords=False"],
            project_check=True,
        )
