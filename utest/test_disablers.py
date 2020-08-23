import pytest

from pathlib import Path

from robocop.utils import DisablersFinder
from robocop.messages import MessageSeverity, Message


@pytest.fixture
def message():
    msg = (
        "somerule",
        "Some description",
        MessageSeverity.WARNING
    )
    return Message('1010', msg)


class TestDisablers:
    def test_disabled_whole_file(self):
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'disabled_whole.robot'), None)
        assert disabler.file_disabled
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'disabled.robot'), None)
        assert not disabler.file_disabled

    def test_is_line_disabled(self):
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'disabled.robot'), None)
        assert disabler.any_disabler
        assert disabler.is_line_disabled(1, 'all')
        assert disabler.is_line_disabled(11, 'somerule')
        assert not disabler.is_line_disabled(11, 'otherule')
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'disabled_whole.robot'), None)
        for i in range(1, 11):
            assert disabler.is_line_disabled(i, 'all')

    @pytest.mark.parametrize('lineno, xor', [
        (2, True),
        (7, True),
        (11, True),
        (12, False)
    ])
    def test_is_msg_disabled(self, lineno, xor, message):
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'disabled.robot'), None)
        message.line = lineno
        assert disabler.is_msg_disabled(message) == xor

    def test_enabled_file(self):
        disabler = DisablersFinder(Path(Path(__file__).parent, 'testdata', 'disabled', 'enabled.robot'), None)
        assert not disabler.any_disabler
