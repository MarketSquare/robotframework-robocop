import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    @pytest.mark.parametrize("config", [None, ["bad-indent.indent=3"]])
    def test_templated_suite(self, config):
        self.check_rule(configure=config, src_files=["templated_suite.robot"], expected_file=None)

    @pytest.mark.parametrize(("file_suffix", "test_on_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_strict_3_spaces(self, file_suffix, test_on_version):
        self.check_rule(
            configure=["bad-indent.indent=3"],
            src_files=["bug375.robot", "comments.robot", "test.robot"],
            expected_file=f"indent_3spaces/expected_output{file_suffix}.txt",
            test_on_version=test_on_version,
        )

    @pytest.mark.parametrize(("file_suffix", "test_on_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_rule(self, file_suffix, test_on_version):
        self.check_rule(
            configure=["bad-indent.indent=-1"],
            src_files=["bug375.robot", "comments.robot", "test.robot"],
            expected_file=f"expected_output{file_suffix}.txt",
            test_on_version=test_on_version,
        )

    def test_extended(self):
        self.check_rule(
            src_files=["bug375.robot", "comments.robot", "test.robot"],
            expected_file="expected_extended.txt",
            output_format="extended",
            test_on_version=">=5",
        )

    def test_758_bug(self):
        self.check_rule(
            configure=["bad-indent.indent=-1"],
            src_files=["bug758/templated_suite.robot"],
            expected_file="bug758/expected_output.txt",
        )

    def test_groups(self):
        self.check_rule(
            src_files=["groups/groups.robot"], expected_file="groups/expected_groups.txt", test_on_version=">=7.2"
        )
