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


def get_message_with_id(msg_id):
    for c in MessageSeverity:
        msg_id = msg_id.replace(c.value, '')
    msg = (
        f"some-message-{msg_id}",
        "Some description",
        MessageSeverity.WARNING
    )
    return Message(msg_id, msg)


class TestIncludingExcluding:
    @pytest.mark.parametrize('included, excluded', [
        (['0101'], ['0102', '0501', '0402']),
        (['W0101', '0102'], ['0501', '0402']),
        (['E0501', 'I0402'], ['0101', '0102'])
    ])
    def test_only_included(self, included, excluded, robocop_instance):
        robocop_instance.config.include.update(set(included))
        robocop_instance.config.remove_severity()
        robocop_instance.config.translate_patterns()
        assert all(robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize('patterns, included, excluded', [
        (['01*'], [], ['0202', '0501', '0403']),
        (['01*', '*5'], ['0101', '0105', '0405'], ['0204', '0402']),
        (['some-message-04*'], ['0401'], ['0101', '0502'])
    ])
    def test_only_included_patterns(self, patterns, included, excluded, robocop_instance):
        robocop_instance.config.include.update(set(patterns))
        robocop_instance.config.remove_severity()
        robocop_instance.config.translate_patterns()
        assert all(robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    @pytest.mark.parametrize('included, excluded', [
        (['0101'], ['0102', '0501', '0402']),
        (['W0101', '0102'], ['0501', '0402']),
        (['E0501', 'I0402'], ['0101', '0102'])
    ])
    def test_only_excluded(self, included, excluded, robocop_instance):
        robocop_instance.config.exclude.update(set(excluded))
        robocop_instance.config.remove_severity()
        robocop_instance.config.translate_patterns()
        assert all(robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in included)
        assert all(not robocop_instance.config.is_rule_enabled(get_message_with_id(msg)) for msg in excluded)

    def test_both_included_excluded(self, robocop_instance):
        robocop_instance.config.include = {'0101'}
        robocop_instance.config.exclude = {'W0101'}
        robocop_instance.config.remove_severity()
        robocop_instance.config.translate_patterns()
        msg = get_message_with_id('0101')
        assert robocop_instance.config.is_rule_disabled(msg)
        assert not robocop_instance.config.is_rule_enabled(msg)
