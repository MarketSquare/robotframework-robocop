import pytest
from pathlib import Path

from robocop import Robocop


@pytest.fixture(scope='session')
def robocop_instance():
    test_data = Path(__file__).parent.parent
    linter = Robocop(from_cli=False)
    linter.config.files = {str(test_data)}
    return linter


def run_rule(name, robocop_instance):
    robocop_instance.config.include = {name}
    robocop_instance.run()


@pytest.mark.benchmark(group='rules')
def test_rule(benchmark, rule, robocop_instance):
    # Rule comes from pytest_generate_tests from conftest.py
    benchmark(run_rule, rule, robocop_instance)
