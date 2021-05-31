from pathlib import Path

import pytest

from robocop.rules import RuleSeverity, Rule
from robocop.utils.disablers import DisablersFinder


@pytest.fixture
def message():
    msg = (
        "somerule",
        "Some description",
        RuleSeverity.WARNING
    )
    return Rule('1010', msg)


class TestDisablers:
    def test_disabled_whole_file(self):
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'disabled_whole.robot'),
            None
        )
        assert disabler.file_disabled
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'disabled.robot'),
            None
        )
        assert not disabler.file_disabled

    def test_is_line_disabled(self):
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'disabled.robot'),
            None
        )
        assert disabler.any_disabler
        assert disabler.is_line_disabled(1, 'all')  # from robocop: disable
        assert disabler.is_line_disabled(11, 'somerule')
        assert disabler.is_line_disabled(13, 'all')  # from noqa
        assert not disabler.is_line_disabled(11, 'otherule')
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'disabled_whole.robot'),
            None
        )
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, 'all')

    def test_is_rule_disabled(self, message):
        # check if rule 1010 is disabled in selected lines
        disabled_lines = {1, 2, 3, 4, 7, 11, 13}
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'disabled.robot'),
            None
        )
        for i in range(1, 14):
            message.line = i
            assert disabler.is_rule_disabled(message) == (i in disabled_lines)

    def test_enabled_file(self):
        disabler = DisablersFinder(
            Path(Path(__file__).parent.parent, 'test_data', 'disabled', 'enabled.robot'),
            None
        )
        assert not disabler.any_disabler
