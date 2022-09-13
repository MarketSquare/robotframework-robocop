from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_bug629_rf3(self):
        self.check_rule(
            config="-c too-few-calls-in-keyword:severity_threshold:warning=1:error=0 -c too-few-calls-in-keyword:min_calls:2",
            src_files=["bug629.robot"],
            expected_file="expected_output_bug629_rf3.txt",
            target_version="==3.2.2",
        )

    def test_bug629_rf4(self):
        self.check_rule(
            config="-c too-few-calls-in-keyword:severity_threshold:warning=1:error=0 -c too-few-calls-in-keyword:min_calls:2",
            src_files=["bug629.robot"],
            expected_file="expected_output_bug629_rf4.txt",
            target_version="==4.1.3",
        )

    def test_bug629(self):
        self.check_rule(
            config="-c too-few-calls-in-keyword:severity_threshold:warning=1:error=0 -c too-few-calls-in-keyword:min_calls:2",
            src_files=["bug629.robot"],
            expected_file="expected_output_bug629.txt",
            target_version=">=5",
        )

    def test_severity_threshold(self):
        self.check_rule(
            config="-c too-few-calls-in-keyword:min_calls:2 -c too-few-calls-in-keyword:severity_threshold:warning=1:error=0",
            src_files=["test.robot"],
            expected_file="expected_output_severity.txt",
        )
