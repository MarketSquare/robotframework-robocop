import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_default_order(self):
        self.check_rule(
            configure=["section-out-of-order.sections_order=settings,keywords,testcases,variables"],
            src_files=["custom_order.robot"],
            expected_file="expected_output_custom_order.txt",
        )

    @pytest.mark.parametrize(
        "sections_order", ["settings,variables,testcases,keywords", "settings,variables,testcases,tasks,keywords"]
    )
    def test_custom_order(self, sections_order):
        self.check_rule(
            configure=[f"section-out-of-order.sections_order={sections_order}"],
            src_files=["test.robot"],
            expected_file="expected_output_default_order.txt",
        )

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")
