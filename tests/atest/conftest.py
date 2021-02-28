import pytest
from robocop.checkers import get_rules_for_atest
from robocop.run import Robocop


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=True)


def pytest_generate_tests(metafunc):
    metafunc.parametrize('rule', get_rules_for_atest())
