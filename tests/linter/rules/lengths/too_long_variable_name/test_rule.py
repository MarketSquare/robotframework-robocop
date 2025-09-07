from tests.linter.utils import RuleAcceptance


class TestRule(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(
            src_files=["test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
        )

    def test_invalid_data(self):
        self.check_rule(
            src_files=["test_invalid.robot"],
            expected_file="expected_extended_invalid.txt",
            output_format="extended",
            test_on_version=">=4.1.2",  # RF decode error prevents testing with earlier versions
        )

    def test_var_dyn(self):
        self.check_rule(
            src_files=["test_var_dyn.robot"],
            expected_file="expected_extended_var_dyn.txt",
            output_format="extended",
            test_on_version=">=7.0",
        )

    def test_except(self):
        self.check_rule(
            src_files=["test_except.robot"],
            expected_file="expected_extended_except.txt",
            output_format="extended",
            test_on_version=">=5.0",
        )

    def test_type(self):
        self.check_rule(
            src_files=["test_type.robot"],
            expected_file="expected_extended_type.txt",
            output_format="extended",
            test_on_version=">=7.3",
        )

    def test_severity_threshold(self):
        self.check_rule(
            configure=[
                "too-long-variable-name.severity_threshold=warning=20:error=40",
                "too-long-variable-name.max_len=20",
            ],
            src_files=["test.robot"],
            expected_file="expected_output_severity_threshold.txt",
        )
