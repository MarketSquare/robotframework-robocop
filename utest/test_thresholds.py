import pytest
import sys
from robocop.run import Robocop
from robocop.messages import MessageSeverity, Message
from robocop.config import Config


class RobocopWithoutLoadClasses(Robocop):
    def __init__(self):  # TODO: move to common file, rewrite init to be reusable in API and unit tests
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.messages = {}
        self.reports = []
        self.disabler = None
        self.config = Config()
        self.config.list = True


@pytest.fixture
def robocop_instance():
    return RobocopWithoutLoadClasses()


def get_severity_enum(value):
    for sev in MessageSeverity:
        if sev.value == value:
            break
    else:
        sev = MessageSeverity.INFO
    return sev


def get_message_with_id_sev(msg_id, sev):
    for c in MessageSeverity:
        msg_id = msg_id.replace(c.value, '')
    sev = get_severity_enum(sev)
    msg = (
        f"some-message-{msg_id}",
        "Some description",
        sev
    )
    return Message(msg_id, msg)


class TestThresholds:
    @pytest.mark.parametrize('threshold, included, excluded', [
        ('F', ['F'], ['I', 'W', 'E']),
        ('E', ['F', 'E'], ['I', 'W']),
        ('W', ['F', 'E', 'W'], ['I']),
        ('I', ['F', 'E', 'W', 'I'], []),
    ])
    def test_disable_messages_below_threshold(self, threshold, included, excluded, robocop_instance):
        robocop_instance.config.threshold = get_severity_enum(threshold)
        for severity in included:
            msg = get_message_with_id_sev('0101', severity)
            assert robocop_instance.config.is_rule_enabled(msg)
        for severity in excluded:
            msg = get_message_with_id_sev('0101', severity)
            assert not robocop_instance.config.is_rule_enabled(msg)
