import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    def test_extended(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_extended.txt", output_format="extended")

    @pytest.mark.parametrize(
        ("test_id", "pattern"),
        [
            (1, r"[$:{}]"),
            (2, r"""[!.?/;+'"()[]{}#$%^&=<>|\]"""),
            (3, r"[^a-zA-Z\s]"),
            (4, r"(?:(?<!foo)\.bar)|(?:foo\.(?!bar))|(?:(?<!foo)\.(?!bar))"),
        ],
    )
    def test_configure_pattern(self, test_id, pattern):
        self.check_rule(
            configure=[f"not-allowed-char-in-name.pattern={pattern}"],
            src_files=[f"configure{test_id}/test.robot"],
            expected_file=f"configure{test_id}/expected_output.txt",
        )
