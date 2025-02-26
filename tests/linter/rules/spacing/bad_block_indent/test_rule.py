import pytest

from tests.linter.utils import RuleAcceptance


class TestRuleAcceptance(RuleAcceptance):
    @pytest.mark.parametrize(("file_suffix", "target_version"), [("", ">=5"), ("_rf4", "==4.*"), ("_rf3", "==3.*")])
    def test_rule(self, file_suffix, target_version):
        self.check_rule(
            expected_file=f"expected_output{file_suffix}.txt",
            target_version=target_version,
        )
