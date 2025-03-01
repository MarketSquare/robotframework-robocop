import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    @pytest.mark.xfail(reason="Project checker needs to be reimplemented")  # FIXME:
    def test_rule(self):
        self.check_rule(src_files=["."], expected_file="expected_output.txt", issue_format="end_col")

    def test_extended(self):
        self.check_rule(src_files=["."], expected_file="expected_extended.txt", output_format="extended")
