import pytest

from robocop.linter.runner import RobocopLinter
from robocop.config import ConfigManager


@pytest.fixture
def empty_linter() -> RobocopLinter:
    config_manager = ConfigManager()
    runner = RobocopLinter(config_manager)
    runner.checkers = []
    runner.rules = {}
    return runner
