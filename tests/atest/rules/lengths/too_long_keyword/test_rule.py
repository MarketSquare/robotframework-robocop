from tests.atest.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self, capsys):
        self.check_rule(capsys, src_files=["test.robot"], expected_file="expected_output.txt")

    def test_ignore_docs(self, capsys):
        self.check_rule(
            capsys,
            config="-c too-long-keyword:ignore_docs:True",
            src_files=["ignore_docs.robot"],
            expected_file="expected_output_ignore_docs.txt",
        )

    def test_severity_threshold(self, capsys):
        self.check_rule(
            capsys,
            config="-c too-long-keyword:severity_threshold:warning=40:error=50",
            src_files=["severity_threshold.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
