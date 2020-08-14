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


@pytest.fixture
def robocop_instance():
    return RobocopWithoutLoadClasses()


class EmptyChecker(VisitorChecker):
    msgs = {}
    pass


class TestListingRules:
    def test_list_rules(self, robocop_instance, capsys):
        checker = EmptyChecker(robocop_instance)
        checker.msgs = {
            '0101': (
                "some-message",
                "Some description",
                MessageSeverity.WARNING
            )
        }
        checker.register_messages(checker.msgs)
        robocop_instance.register_checker(checker)
        with pytest.raises(SystemExit) as err:
            robocop_instance.list_checkers()
        out, _ = capsys.readouterr()
        assert "0101" in out
