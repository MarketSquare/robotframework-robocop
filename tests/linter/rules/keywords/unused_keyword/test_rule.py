import pytest

from tests.linter.utils import RuleAcceptance


@pytest.mark.skip("Skipped: unused-keyword is temporarily disabled")
class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["."], expected_file="expected_output.txt", issue_format="end_col")

    def test_extended(self):
        self.check_rule(src_files=["."], expected_file="expected_extended.txt", output_format="extended")
