from pathlib import Path

import pytest
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
                break
        else:
            pytest.exit(f"Rule: '{selected_rule}' was not found", 1)
        metafunc.parametrize('rule, args, test_data', [(selected_rule, args, test_data)])
        return
    # TODO: load other tests from file (like yaml)
    auto_discovered_rules.append((
        'inconsistent-assignment',
        ['-c', 'inconsistent-assignment:assignment_sign_type:space_and_equal_sign'],
        'misc/inconsistent-assignment-const'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment-in-variables',
        ['-c', 'inconsistent-assignment-in-variables:assignment_sign_type:space_and_equal_sign'],
        'misc/inconsistent-assignment-in-variables-const'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment',
        ['-c', 'inconsistent-assignment:assignment_sign_type:autodetect'],
        'misc/inconsistent-assignment-autodetect'
    ))
    auto_discovered_rules.append((
        'inconsistent-assignment-in-variables',
        ['-c', 'inconsistent-assignment-in-variables:assignment_sign_type:autodetect'],
        'misc/inconsistent-assignment-in-variables-autodetect'
    ))
    auto_discovered_rules.append((
        'wrong-case-in-keyword-name',
        ['-c', 'wrong-case-in-keyword-name:convention:first_word_capitalized'],
        'naming/wrong-case-in-keyword-name-first-word'
    ))
    metafunc.parametrize('rule, args, test_data', auto_discovered_rules)
