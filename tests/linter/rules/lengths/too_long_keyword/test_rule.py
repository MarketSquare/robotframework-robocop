from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    def test_ignore_docs(self):
        self.check_rule(
            configure=["too-long-keyword.ignore_docs=True"],
            src_files=["ignore_docs.robot"],
            expected_file="expected_output_ignore_docs.txt",
        )

    def test_severity_threshold(self):
        self.check_rule(
            configure=["too-long-keyword.severity_threshold=warning=40:error=50"],
            src_files=["severity_threshold.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
