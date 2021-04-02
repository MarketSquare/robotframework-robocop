from pathlib import Path

import pytest
from robocop.checkers import get_rules_for_atest
from robocop.run import Robocop, Config


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=True)


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
    metafunc.parametrize('rule, args, test_data', auto_discovered_rules)


def preconfigured_robocop(rules, sources):
    runner = Robocop(from_cli=True)
    config = Config()
    config.parse_opts([
        '--include',
        ','.join(rules),
        '--format',
        '{source}:{line}:{col} [{severity}] {rule_id} {desc}',
        '--configure',
        'return_status:quality_gate:E=0:W=0:I=0',
        *sources
     ])
    runner.config = config
    return runner
