import sys
from pathlib import Path

import pytest

from robocop.run import Robocop
from robocop.config import Config
import robocop.exceptions


class RobocopWithoutLoadClasses(Robocop):
    def __init__(self):
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.messages = {}
        self.reports = []
        self.disabler = None
        self.config = Config()


@pytest.fixture
def robocop_instance():
    return RobocopWithoutLoadClasses()


class TestExternalRules:
    def test_loading_external_rule(self, robocop_instance):  # noqa
        robocop_instance.config.ext_rules = {f'{Path(__file__).parent}/testdata/rule/external_rule.py'}
        robocop_instance.load_checkers()
        assert "1101" in robocop_instance.messages

    def test_loading_multiple_external_rules(self, robocop_instance):  # noqa
        robocop_instance.config.ext_rules = {
            f'{Path(__file__).parent}/testdata/rule/external_rule.py',
            f'{Path(__file__).parent}/testdata/rule/external_rule2.py'
        }
        robocop_instance.load_checkers()
        assert "1101" in robocop_instance.messages
        assert "1102" in robocop_instance.messages

    def test_loading_external_rule_dir(self, robocop_instance):  # noqa
        robocop_instance.config.ext_rules = {f'{Path(__file__).parent}/testdata/rule/'}
        robocop_instance.load_checkers()
        assert "1101" in robocop_instance.messages
        assert "1102" in robocop_instance.messages

    def test_loading_non_existing_rule(self, robocop_instance):  # noqa
        robocop_instance.config.ext_rules = {f'{Path(__file__).parent}/testdata/rule/non_existing.py'}
        with pytest.raises(robocop.exceptions.InvalidExternalCheckerError) as err:
            robocop_instance.load_checkers()
        assert "Fatal error: Failed to load external rules from file" in str(err)

    def test_loading_duplicated_rule(self, robocop_instance):  # noqa
        robocop_instance.config.ext_rules = {
            f'{Path(__file__).parent}/testdata/rule/external_rule.py',
            f'{Path(__file__).parent}/testdata/rule_duplicate/external_rule_dup.py'
        }
        with pytest.raises(robocop.exceptions.DuplicatedMessageError) as err:
            robocop_instance.load_checkers()
        assert "Fatal error: Message name 'smth' defined in SmthChecker was already defined in SmthChecker" in str(err)
