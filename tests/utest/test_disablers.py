from pathlib import Path

import pytest
from robot.api import get_model

from robocop import Config, Robocop
from robocop.rules import Message, Rule, RuleParam, RuleSeverity
from robocop.utils.disablers import DisablersFinder
from robocop.utils.misc import ROBOT_VERSION
from robocop.utils.version_matching import Version


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
        msg=rule.get_message(),
        source=None,
        node=None,
        lineno=None,
        col=None,
        end_lineno=None,
        end_col=None,
    )


DISABLED_TEST_DIR = Path(__file__).parent.parent / "test_data" / "disabled"


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
    def test_disabled_whole_file(self):
        model = get_model(DISABLED_TEST_DIR / "disabled_whole.robot")
        disabler = DisablersFinder(model)
        assert disabler.file_disabled
        model = get_model(DISABLED_TEST_DIR / "disabled.robot")
        disabler = DisablersFinder(model)
        assert not disabler.file_disabled

    def test_is_line_disabled(self):
        model = get_model(DISABLED_TEST_DIR / "disabled.robot")
        disabler = DisablersFinder(model)
        assert disabler.any_disabler
        assert disabler.is_line_disabled(10, "somerule")
        assert disabler.is_line_disabled(12, "all")  # from noqa
        assert not disabler.is_line_disabled(10, "otherule")
        model = get_model(DISABLED_TEST_DIR / "disabled_whole.robot")
        disabler = DisablersFinder(model)
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, "all")

    def test_is_rule_disabled(self, message):
        # check if rule 1010 is disabled in selected lines
        exp_disabled_lines = {6, 10, 12}
        model = get_model(DISABLED_TEST_DIR / "disabled.robot")
        disabler = DisablersFinder(model)
        disabled_lines = set()
        for i in range(1, 14):
            message.line = i
            if disabler.is_rule_disabled(message):
                disabled_lines.add(i)
        assert disabled_lines == exp_disabled_lines

    def test_enabled_file(self):
        model = get_model(DISABLED_TEST_DIR / "enabled.robot")
        disabler = DisablersFinder(model)
        assert not disabler.any_disabler

    @pytest.mark.parametrize("file", [1, 2, 3])
    def test_extended_disabling(self, file):
        source = DISABLED_TEST_DIR / f"extended_lines{file}.robot"
        with open(source) as f:
            data = f.read()
        issues = run_check_on_string(data, include={"too-long-keyword"}, configure=["too-long-keyword:max_len:1"])
        assert not issues

    def test_disabling_after_keyword(self):
        source = DISABLED_TEST_DIR / "extended_lines4.robot"
        with open(source) as f:
            data = f.read()
        issues = run_check_on_string(data, include={"too-long-keyword"}, configure=["too-long-keyword:max_len:1"])
        assert issues

    @pytest.mark.skipif(ROBOT_VERSION < Version("5.0"), reason="Test with RF 5.0 syntax")  # noqa: SIM300
    def test_disablers_in_scopes(self):
        model = get_model(DISABLED_TEST_DIR / "scopes.robot")
        disabler = DisablersFinder(model)
        exp_disabled_rules = {
            "all": [(8, 9)],
            "rule1": [(4, 9), (39, 39), (72, 72)],
            "rule2": [(14, 42), (32, 41), (47, 74), (65, 74)],
            "rule3": [(22, 29), (55, 62)],
            "rule4": [(24, 25), (57, 58)],
        }
        disabled_rules = {rule_name: sorted(rule.blocks) for rule_name, rule in disabler.disabled.rules.items()}
        assert disabled_rules == exp_disabled_rules
