import pytest
from robocop.checkers import get_rules_for_atest
from robocop.run import Robocop


@pytest.fixture
def robocop_instance():
    return Robocop()


def pytest_generate_tests(metafunc):
    rules = [rule for rule in get_rules_for_atest()]
    metafunc.parametrize('rule', rules)
