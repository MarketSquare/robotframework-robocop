from pathlib import Path

import pytest
from robot.api import get_model

from robocop import Config, Robocop
from robocop.rules import Message, Rule, RuleParam, RuleSeverity
from robocop.utils.disablers import DisablersFinder


@pytest.fixture
def message():
    rule = Rule(
        RuleParam(name="param_name", converter=int, default=1, desc=""),
        rule_id="1010",
        name="somerule",
        msg="Some description",
        severity=RuleSeverity.WARNING,
    )
    return Message(
        rule=rule,
        source=None,
        node=None,
        lineno=None,
        col=None,
        end_lineno=None,
        end_col=None,
    )


@pytest.fixture
def disablers_test_data():
    return Path(Path(__file__).parent.parent, "test_data", "disabled")


def run_check_on_string(in_memory, include=None, configure=None):
    if include is None:
        include = set()
    if configure is None:
        configure = []
    config = Config(root=str(Path(__file__).parent))
    config.include = include
    config.configure = configure
    robocop_runner = Robocop(config=config)
    robocop_runner.reload_config()

    ast_model = get_model(in_memory)
    return robocop_runner.run_check(ast_model, r"C:\directory\file.robot", in_memory)


class TestDisablers:
    def test_disabled_whole_file(self, disablers_test_data):
        disabler = DisablersFinder(disablers_test_data / "disabled_whole.robot", None)
        assert disabler.file_disabled
        disabler = DisablersFinder(disablers_test_data / "disabled.robot", None)
        assert not disabler.file_disabled

    def test_is_line_disabled(self, disablers_test_data):
        disabler = DisablersFinder(disablers_test_data / "disabled.robot", None)
        assert disabler.any_disabler
        assert disabler.is_line_disabled(1, "all")  # from robocop: disable
        assert disabler.is_line_disabled(11, "somerule")
        assert disabler.is_line_disabled(13, "all")  # from noqa
        assert not disabler.is_line_disabled(11, "otherule")
        disabler = DisablersFinder(disablers_test_data / "disabled_whole.robot", None)
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, "all")

    def test_is_rule_disabled(self, message, disablers_test_data):
        # check if rule 1010 is disabled in selected lines
        disabled_lines = {1, 2, 3, 4, 7, 11, 13}
        disabler = DisablersFinder(disablers_test_data / "disabled.robot", None)
        for i in range(1, 14):
            message.line = i
            assert disabler.is_rule_disabled(message) == (i in disabled_lines)

    def test_enabled_file(self, disablers_test_data):
        disabler = DisablersFinder(disablers_test_data / "enabled.robot", None)
        assert not disabler.any_disabler

    @pytest.mark.parametrize("file", [1, 2, 3, 4])
    def test_extended_disabling(self, file, disablers_test_data):
        source = disablers_test_data / f"extended_lines{file}.robot"
        with open(source) as f:
            data = f.read()
        issues = run_check_on_string(data, include={"too-long-keyword"}, configure=["too-long-keyword:max_len:1"])
        assert not issues
