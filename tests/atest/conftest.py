from pathlib import Path

import pytest
from robocop.checkers import get_rules_for_atest
from robocop.run import Robocop


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
    # TODO: load other tests from file (like yaml)
    auto_discovered_rules.append((
        'inconsistent-assignment-sign',
        ['-c', 'inconsistent-assignment-sign:assignment_sign_type:space_and_equal_sign'],
        'misc/inconsistent-assignment-sign-const'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment-sign-variables',
        ['-c', 'inconsistent-assignment-sign-variables:assignment_sign_type:space_and_equal_sign'],
        'misc/inconsistent-assignment-sign-variables-const'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment-sign',
        ['-c', 'inconsistent-assignment-sign:assignment_sign_type:autodetect'],
        'misc/inconsistent-assignment-sign-autodetect'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment-sign-variables',
        ['-c', 'inconsistent-assignment-sign-variables:assignment_sign_type:autodetect'],
        'misc/inconsistent-assignment-sign-variables-autodetect'
    ))
    metafunc.parametrize('rule, args, test_data', auto_discovered_rules)
