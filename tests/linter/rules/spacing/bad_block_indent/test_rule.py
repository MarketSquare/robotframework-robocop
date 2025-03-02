import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    @pytest.mark.parametrize(("file_suffix", "test_on_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_rule(self, file_suffix, test_on_version):
        self.check_rule(
            src_files=["comments.robot", "test.robot"],
            expected_file=f"expected_output{file_suffix}.txt",
            test_on_version=test_on_version,
        )

    def test_groups(self):
        self.check_rule(src_files=["groups.robot"], expected_file="expected_groups.txt", test_on_version=">=7.2")

    def test_extended(self):
        self.check_rule(
            src_files=["comments.robot", "test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5",
        )
