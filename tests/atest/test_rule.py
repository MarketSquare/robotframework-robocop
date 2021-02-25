import pytest
from pathlib import Path
import os
from robocop.config import Config
from robocop.utils import IS_RF4, DISABLED_IN_4


def configure_robocop_with_rule(runner, rule, path):
    config = Config()
    config.parse_opts([
        '--include',
        rule,
        '--format',
        '{source}:{line}:{col} [{severity}] {rule_id} {desc}',
        '--configure',
        'return_status:quality_gate:E=0:W=0:I=0',
        str(path)
     ])
    runner.config = config
    runner.checkers = []
    runner.rules = {}
    runner.load_checkers()
    runner.load_reports()
    runner.configure_checkers_or_reports()
    return runner


def replace_paths(line, rules_dir):
    return line.replace('${rules_dir}', rules_dir).replace(r'${\}', os.path.sep).rstrip('\n')


def test_rule(rule, robocop_instance, capsys):
    """ To run one rule instead of all run::

        pytest -k test_rule[rule_name] tests/atest

    """
    if IS_RF4 and rule in DISABLED_IN_4:
        return
    current_dir = Path(__file__).parent
    test_data = Path(current_dir, 'rules', rule)
    expected_output = Path(test_data, 'expected_output.txt')
    assert test_data.exists(), f"Missing test data for rule '{rule}'"
    assert expected_output.exists(), f"Missing expected_output.txt file for rule '{rule}'"
    with open(expected_output) as f:
        expected = [replace_paths(line, str(test_data)) for line in f]
    robocop_instance = configure_robocop_with_rule(robocop_instance, rule, test_data)
    with pytest.raises(SystemExit) as system_exit:
        robocop_instance.run()
    assert system_exit.value.code > 0  # if any error issue found there should be > 0 exit code
    out, _ = capsys.readouterr()
    actual = out.splitlines()
    assert sorted(actual) == sorted(expected)
