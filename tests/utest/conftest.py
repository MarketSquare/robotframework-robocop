import sys

import pytest

from robocop.config import Config
from robocop.run import Robocop


@pytest.fixture
def robocop_instance():
    return Robocop()


class RobocopWithoutLoadClasses(Robocop):
    def __init__(self):
        self.files = {}
        self.checkers = []
        self.out = sys.stdout
        self.rules = {}
        self.reports = []
        self.disabler = None
        self.config = Config()


@pytest.fixture
def robocop_pre_load():
    return RobocopWithoutLoadClasses()
