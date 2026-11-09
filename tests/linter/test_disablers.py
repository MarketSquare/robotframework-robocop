import io
from pathlib import Path

import pytest
from robot.api import get_model

from robocop.linter.diagnostics import Diagnostic
from robocop.linter.rules.lengths import LineTooLongRule
from robocop.linter.utils.disablers import DisablersFinder, DisablersVisitor
from robocop.version_handling import ROBOT_VERSION, Version


@pytest.fixture
def diagnostic() -> Diagnostic:
    return Diagnostic(
        rule=LineTooLongRule(), source="", lineno=0, col=0, end_lineno=None, end_col=None, node=None, model=None
    )


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
        assert disabler.is_line_disabled(15, "disable-whole-keyword")
        assert disabler.is_line_disabled(16, "disable-whole-keyword")
        assert not disabler.is_line_disabled(17, "disable-whole-keyword")
        assert disabler.is_line_disabled(23, "whole-section")
        assert disabler.is_line_disabled(24, "whole-section")
        assert disabler.is_line_disabled(25, "whole-section")
        assert not disabler.is_line_disabled(19, "all")
        assert not disabler.is_line_disabled(19, "some-rule")
        assert not disabler.is_line_disabled(20, "all")
        model = get_model(DISABLED_TEST_DIR / "disabled_whole.robot")
        disabler = DisablersFinder(model)
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, "all")

    def test_is_rule_disabled(self, diagnostic):
        # check if rule 1010 is disabled in selected lines
        exp_disabled_lines = {6, 7, 8, 10, 11, 12, 13}
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
            "rule2": [(14, 42), (32, 41), (47, 78), (65, 74)],
            "rule3": [(22, 29), (55, 62)],
            "rule4": [(24, 25), (57, 58)],
        }
        disabled_rules = {
            rule_name: sorted([(block.start_line, block.end_line) for block in rule.blocks])
            for rule_name, rule in disabler.visitor.rules.items()
        }
        assert disabled_rules == exp_disabled_rules

    def test_mixed_disablers(self):
        # Arrange
        model = get_model(DISABLED_TEST_DIR / "mixed_disablers.robot")
        disabler = DisablersFinder(model)
        exp_disabled_rules = {
            "all": [4, 5, 7, 8, 11, 12, 13, 15],
            "rule": [3, 6, 14],
            "rule1": [15, 16, 17, 18],
            "rule2": [14, 15, 16, 17],
        }

        # Act
        disabled_rules = {rule_name: sorted(rule.lines) for rule_name, rule in disabler.visitor.rules.items()}

        # Assert
        assert disabled_rules == exp_disabled_rules


def read_lines(path: Path) -> list[str]:
    with path.open(encoding="utf-8", newline="") as file:
        return file.readlines()


def found_rules(disabler: DisablersFinder) -> dict:
    if disabler.visitor is None:
        return {}
    return {
        rule_name: (sorted(rule.lines), [(block.start_line, block.end_line) for block in rule.blocks])
        for rule_name, rule in disabler.visitor.rules.items()
    }


@pytest.mark.parametrize("test_file", ["disabled.robot", "disabled_whole.robot", "mixed_disablers.robot"])
def test_find_disablers_with_source_lines(test_file):
    model = get_model(DISABLED_TEST_DIR / test_file)
    expected = DisablersFinder(model)
    disabler = DisablersFinder(model, read_lines(DISABLED_TEST_DIR / test_file))
    assert found_rules(disabler) == found_rules(expected)
    assert disabler.file_disabled == expected.file_disabled


def test_model_without_disablers_is_not_visited(monkeypatch):
    source = "*** Test Cases ***\nTest\n    # robocop  noqa\n    Keyword    # comment\n"
    model = get_model(io.StringIO(source))
    monkeypatch.setattr(DisablersVisitor, "visit", lambda *_: pytest.fail("model should not be visited"))
    disabler = DisablersFinder(model, source.splitlines(keepends=True))
    assert not disabler.any_disabler
    assert not disabler.file_disabled
    assert not disabler.is_line_disabled(3, "all")
    assert list(disabler.not_used_disablers) == []
