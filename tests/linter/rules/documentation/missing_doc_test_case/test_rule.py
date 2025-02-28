from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(expected_file="expected_extended.txt", output_format="extended")

    def test_templated(self):
        self.check_rule(
            configure=["missing-doc-test-case.ignore_templated=False"],
            src_files=["templated.robot"],
            expected_file="expected_output_templated.txt",
        )

    def test_templated_turned_off(self):
        self.check_rule(
            configure=["missing-doc-test-case.ignore_templated=True"],
            src_files=["templated.robot"],
            expected_file=None,
        )
