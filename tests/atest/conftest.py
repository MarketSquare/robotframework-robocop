from pathlib import Path

import pytest
import yaml

from robocop.checkers import get_rules
from robocop.run import Robocop


@pytest.fixture
def robocop_instance():
    return Robocop(from_cli=False)


def pytest_addoption(parser):
    parser.addoption("--rule", action="store")


def pytest_generate_tests(metafunc):
    """This method generate tests based on template ``test_rule``.

    Rules are autodiscovered. You can add your own tests by adding tuple with test data to ``auto_discovered_rules``
    list. This tuple should contain:
    ('name_of_rule_to_be_included', ['list', 'of', 'cli', 'extra', 'args'], 'path/to/src/and/expected inside rules dir')

    For example::

        ('line-too-long', ['--configure', 'line-too-long:line_length:1'], 'lengths/line-too-long')

    """
    if "rule" not in metafunc.fixturenames:
        return
    rules = {rule.name: (category, rule) for category, rule in get_rules()}
    selected_rule = metafunc.config.getoption("--rule", None)
    if selected_rule is not None:
        # Find and use only selected rule
        if selected_rule in rules:
            rule, category = rules[selected_rule]
            metafunc.parametrize(
                "rule, args, test_data, enabled",
                [(selected_rule, None, f"{category}/{rule.name}", rule.enabled_in_version)],
            )
            return
        else:
            pytest.exit(f"Rule: '{selected_rule}' was not found", 1)
    configured_tests = [
        (rule.name, None, f"{category}/{rule.name}", rule.enabled_in_version) for (category, rule) in rules.values()
    ]
    with open(Path(__file__).parent / "custom_tests.yaml") as f:
        tests = yaml.safe_load(f)
    for rule, configs in tests["tests"].items():
        for config in configs:
            configuration = ["-c", config["config"]] if config["config"] else []
            if rule in rules:
                configured_tests.append((rule, configuration, config["src_dir"], rules[rule][1].enabled_in_version))
            else:
                pytest.exit(f"Rule: '{rule}' was not found", 1)
    metafunc.parametrize("rule, args, test_data, enabled", configured_tests)
