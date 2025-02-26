import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    @pytest.mark.parametrize("config", [None, "-c bad-indent:indent:3"])
    def test_templated_suite(self, config):
        self.check_rule(config=config, src_files=["templated_suite.robot"], expected_file=None)

    @pytest.mark.parametrize(("file_suffix", "target_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_strict_3_spaces(self, file_suffix, target_version):
        self.check_rule(
            config="-c bad-indent:indent:3",
            src_files=["bug375.robot", "comments.robot", "test.robot"],
            expected_file=f"indent_3spaces/expected_output{file_suffix}.txt",
            target_version=target_version,
        )

    @pytest.mark.parametrize(("file_suffix", "target_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_rule(self, file_suffix, target_version):
        self.check_rule(
            config="-c bad-indent:indent:-1",
            src_files=["bug375.robot", "comments.robot", "test.robot"],
            expected_file=f"expected_output{file_suffix}.txt",
            target_version=target_version,
        )

    def test_758_bug(self):
        self.check_rule(
            config="-c bad-indent:indent:-1",
            src_files=["bug758/templated_suite.robot"],
            expected_file="bug758/expected_output.txt",
        )
