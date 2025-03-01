from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_ignore_docs(self):
        self.check_rule(
            configure=["too-long-test-case.ignore_docs=True"],
            src_files=["test.robot"],
            expected_file="expected_output_ignore_docs.txt",
        )

    def test_severity(self):
        self.check_rule(
            # FIXME: There is issue where previous rule configuration remains even with new Robocop instance
            # that's why we need to 'unset' ignore_docs parameter value
            configure=[
                "too-long-test-case.ignore_docs=False",
                "too-long-test-case.severity_threshold=error=20",
                "too-long-test-case.max_len=10",
            ],
            src_files=["severity.robot"],
            expected_file="expected_output_severity.txt",
        )
