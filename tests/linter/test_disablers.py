from pathlib import Path

import pytest
from robot.api import get_model

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.rules.lengths import LineTooLongRule
from robocop.linter.utils.disablers import DisablersFinder
from robocop.linter.utils.misc import ROBOT_VERSION
from robocop.linter.utils.version_matching import Version


@pytest.fixture
def diagnostic() -> Diagnostic:
    return Diagnostic(rule=LineTooLongRule(), source="", lineno=0, col=0, end_lineno=None, end_col=None, node=None)


DISABLED_TEST_DIR = Path(__file__).parent / "test_data" / "disablers"


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
        assert disabler.is_line_disabled(10, "line-too-long")
        assert disabler.is_line_disabled(12, "all")  # from noqa
        assert not disabler.is_line_disabled(10, "otherule")
        model = get_model(DISABLED_TEST_DIR / "disabled_whole.robot")
        disabler = DisablersFinder(model)
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, "all")

    def test_is_rule_disabled(self, diagnostic):
        # check if rule 1010 is disabled in selected lines
        exp_disabled_lines = {6, 10, 12}
        model = get_model(DISABLED_TEST_DIR / "disabled.robot")
        disabler = DisablersFinder(model)
        disabled_lines = set()
        for i in range(1, 14):
            diagnostic.range.start.line = i
            if disabler.is_rule_disabled(diagnostic):
                disabled_lines.add(i)
        assert disabled_lines == exp_disabled_lines

    def test_enabled_file(self):
        model = get_model(DISABLED_TEST_DIR / "enabled.robot")
        disabler = DisablersFinder(model)
        assert not disabler.any_disabler

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
