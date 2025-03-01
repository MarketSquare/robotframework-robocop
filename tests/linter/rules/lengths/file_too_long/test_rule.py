import pytest

from robocop.linter.rules import RuleSeverity
from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    # TODO: we also need to ensure that --threshold E translates to RuleSeverity.Error (there should be ut for it)
    @pytest.mark.parametrize("filter_threshold", [None, RuleSeverity.ERROR, RuleSeverity.WARNING])
    def test_severity_threshold(self, filter_threshold):
        if filter_threshold == RuleSeverity.ERROR:
            expected_output = "expected_output_severity_threshold_only_error.txt"
        else:
            expected_output = "expected_output_severity_threshold.txt"
        self.check_rule(
            configure=["file-too-long.max_lines=300", "file-too-long.severity_threshold=warning=300:error=400"],
            threshold=filter_threshold,
            src_files=["shorter.robot", "longer.robot"],
            expected_file=expected_output,
        )
