import pytest

from robocop.utils.misc import ROBOT_VERSION
from tests.atest.utils import RuleAcceptance


@pytest.fixture
def expected_data_dir():
    if ROBOT_VERSION.major == 3:
        return "if_not_supported"
    return "if_supported"


class TestRuleAcceptance(RuleAcceptance):
    def test_rule(self, expected_data_dir):
        self.check_rule(src_files=["test.robot"], expected_file=f"{expected_data_dir}/expected_output.txt")

    def test_rule_1s(self, expected_data_dir):
        self.check_rule(
            config="-c sleep-keyword-used:max_time:1s",
            src_files=["test.robot"],
            expected_file=f"{expected_data_dir}/expected_output_1s.txt",
        )

    def test_rule_1min(self, expected_data_dir):
        self.check_rule(
            config="-c sleep-keyword-used:max_time:1min",
            src_files=["test.robot"],
            expected_file=f"{expected_data_dir}/expected_output_1min.txt",
        )
