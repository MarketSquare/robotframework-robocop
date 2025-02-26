import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    @pytest.mark.parametrize("filter_threshold", [None, "E", "W"])
    def test_severity_threshold(self, filter_threshold):
        config = "-c file-too-long:max_lines:300 -c file-too-long:severity_threshold:warning=300:error=400"
        if filter_threshold:
            config += f" -t {filter_threshold}"
        if filter_threshold == "E":
            expected_output = "expected_output_severity_threshold_only_error.txt"
        else:
            expected_output = "expected_output_severity_threshold.txt"
        self.check_rule(
            config=config,
            src_files=["shorter.robot", "longer.robot"],
            expected_file=expected_output,
        )
