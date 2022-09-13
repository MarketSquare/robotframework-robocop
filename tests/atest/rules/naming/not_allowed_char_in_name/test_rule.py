import pytest

from tests.atest.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self):
        self.check_rule(src_files=["test.robot"], expected_file="expected_output.txt")

    @pytest.mark.parametrize(
        "test_id, pattern",
        [
            (1, "[$:{}]"),
            (2, """[!.?/;+'"()[]{}#$%^&=<>|\]"""),
            (3, "[^a-zA-Z\s]"),
            (4, "(?:(?<!foo)\.bar)|(?:foo\.(?!bar))|(?:(?<!foo)\.(?!bar))"),
        ],
    )
    def test_configure_pattern(self, test_id, pattern):
        self.check_rule(
            config=f"-c not-allowed-char-in-name:pattern:{pattern}",
            src_files=[f"configure{test_id}/test.robot"],
            expected_file=f"configure{test_id}/expected_output.txt",
        )
