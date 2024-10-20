import pytest

from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_ignore_docs(self):
        self.check_rule(
            config="-c misaligned-continuation-row:ignore_docs:False",
            src_files=["test.robot"],
            expected_file="expected_output_ignore_docs.txt",
        )

    @pytest.mark.parametrize(
        "ignore_run_keywords, expected_file",
        [(True, "expected_output_run_kw.txt"), (False, "expected_output_run_kw_off.txt")],
    )
    def test_run_keyword(self, ignore_run_keywords, expected_file):
        self.check_rule(
            config=f"-c misaligned-continuation-row:ignore_run_keywords:{ignore_run_keywords}",
            src_files=["run_keyword.robot"],
            expected_file=expected_file,
        )
