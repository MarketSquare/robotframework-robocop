import pytest

from robocop.config import ConfigManager
from robocop.linter.runner import RobocopLinter


@pytest.fixture
def empty_linter() -> RobocopLinter:
    config_manager = ConfigManager()
    runner = RobocopLinter(config_manager)
    runner.config.linter._checkers = []  # noqa: SLF001
    runner.config.linter._rules = {}  # noqa: SLF001
    return runner


@pytest.fixture(scope="session")
def loaded_linter() -> RobocopLinter:
    config_manager = ConfigManager()
    return RobocopLinter(config_manager)
