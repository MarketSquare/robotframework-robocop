import pytest
import yaml
from pathlib import Path
from robocop.checkers import get_rules_for_atest
from robocop.run import Robocop


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=False)


def pytest_addoption(parser):
    parser.addoption("--rule", action="store")


def pytest_generate_tests(metafunc):
    """ This method generate tests based on template ``test_rule``.

    Rules are autodiscovered. You can add your own tests by adding tuple with test data to ``auto_discovered_rules``
    list. This tuple should contain:
    ('name_of_rule_to_be_included', ['list', 'of', 'cli', 'extra', 'args'], 'path/to/src/and/expected inside rules dir')

    For example::

        ('line-too-long', ['--configure', 'line-too-long:line_length:1'], 'lengths/line-too-long')

    """
    if "rule" not in metafunc.fixturenames:
        return
    auto_discovered_rules = [(rule, None, f"{category}/{rule}") for category, rule in get_rules_for_atest()]
    selected_rule = metafunc.config.getoption('--rule', None)
    if selected_rule is not None:
        # Find and use only selected rule
        for rule, args, test_data in auto_discovered_rules:
            if rule == selected_rule:
                metafunc.parametrize('rule, args, test_data', [(selected_rule, args, test_data)])
                break
        else:
            pytest.exit(f"Rule: '{selected_rule}' was not found", 1)
        return
    with open(Path(__file__).parent / 'custom_tests.yaml') as f:
        tests = yaml.safe_load(f)
    for rule, configs in tests['tests'].items():
        for config in configs:
            auto_discovered_rules.append((rule, ['-c', config['config']], config['src_dir']))
    metafunc.parametrize('rule, args, test_data', auto_discovered_rules)
