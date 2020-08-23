import sys

import pytest
from robocop.run import Robocop
from robocop.config import Config
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


class RobocopWithoutLoadClasses(Robocop):
    def __init__(self):
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.messages = {}
        self.reports = []
        self.disabler = None
        self.config = Config()
        self.config.list = True
        
        
class EmptyChecker(VisitorChecker):
    msgs = {}
    pass


@pytest.fixture
def robocop_instance():
    return RobocopWithoutLoadClasses()


@pytest.fixture
def msg_0101():
    return {
        '0101': (
            "some-message",
            "Some description",
            MessageSeverity.WARNING
        )
    }


@pytest.fixture
def msg_0102_0204():
    return {
        '0102': (
            'other-message',
            '''this is description''',
            MessageSeverity.ERROR
        ),
        '0204': (
            "another message",
            f"Message with meaning {4}",
            MessageSeverity.INFO
        )
    }


def init_empty_checker(robocop_instance, msg, exclude=False):
    checker = EmptyChecker(robocop_instance)
    checker.msgs = msg
    checker.register_messages(checker.msgs)
    if exclude:
        robocop_instance.config.exclude.update(set(msg.keys()))
        robocop_instance.config.translate_patterns()
    robocop_instance.register_checker(checker)
    return checker


class TestListingRules:
    def test_list_rule(self, robocop_instance, msg_0101, capsys):
        init_empty_checker(robocop_instance, msg_0101)
        with pytest.raises(SystemExit):
            robocop_instance.list_checkers()
        out, _ = capsys.readouterr()
        assert out == 'Message - 0101 [W]: some-message: Some description (enabled)\n'

    def test_list_disabled_rule(self, robocop_instance, msg_0101, capsys):
        init_empty_checker(robocop_instance, msg_0101, exclude=True)
        with pytest.raises(SystemExit):
            robocop_instance.list_checkers()
        out, _ = capsys.readouterr()
        assert out == 'Message - 0101 [W]: some-message: Some description (disabled)\n'

    def test_multiple_checkers(self, robocop_instance, msg_0101, msg_0102_0204, capsys):
        init_empty_checker(robocop_instance, msg_0102_0204, exclude=True)
        init_empty_checker(robocop_instance, msg_0101)
        with pytest.raises(SystemExit):
            robocop_instance.list_checkers()
        out, _ = capsys.readouterr()
        exp_msg = (
            'Message - 0101 [W]: some-message: Some description (enabled)\n',
            'Message - 0102 [E]: other-message: this is description (disabled)\n',
            'Message - 0204 [I]: another message: Message with meaning 4 (disabled)\n'
        )
        assert all(msg in out for msg in exp_msg)
