import pytest
from pathlib import Path
import os
from robocop.config import Config
from robocop.utils import IS_RF4, DISABLED_IN_4, ENABLED_IN_4


def configure_robocop_with_rule(args, runner, rule, path):
    config = Config()
    config.parse_opts([
        '--include',
        rule,
        '--format',
        '{source}:{line}:{col} [{severity}] {rule_id} {desc}',
        '--configure',
        'return_status:quality_gate:E=0:W=0:I=0',
        *args,
        str(path)
     ])
    runner.config = config
    return runner


def replace_paths(line, rules_dir):
    return line.replace('${rules_dir}', rules_dir).replace(r'${\}', os.path.sep).rstrip('\n')


def find_test_data(test_data_path, rule):
    current_dir = Path(__file__).parent
    test_data = Path(current_dir, 'rules', test_data_path)
    if IS_RF4:
        expected_output = Path(test_data, 'expected_output_rf4.txt')
        if not expected_output.exists():
            expected_output = Path(test_data, 'expected_output.txt')
    else:
        expected_output = Path(test_data, 'expected_output.txt')
    assert test_data.exists(), f"Missing test data for rule '{rule}'"
    assert expected_output.exists(), f"Missing expected_output.txt file for rule '{rule}'"
    return test_data, expected_output


def load_expected_file(expected_file, src):
    with open(expected_file) as f:
        return [replace_paths(line, str(src)) for line in f]


def test_rule(rule, args, test_data, robocop_instance, capsys):
    """ To run one rule instead of all run::

        pytest -k test_rule[rule_name] tests/atest

    """
    args = args if args is not None else []
    src, expected_file = find_test_data(test_data, rule)
    expected = load_expected_file(expected_file, src)
    robocop_instance = configure_robocop_with_rule(args, robocop_instance, rule, src)
    with pytest.raises(SystemExit) as system_exit:
        robocop_instance.run()
    if (IS_RF4 and rule in DISABLED_IN_4) or (not IS_RF4 and rule in ENABLED_IN_4):
        assert system_exit.value.code == 0
    else:
        assert system_exit.value.code > 0  # if any error issue found there should be > 0 exit code
        out, _ = capsys.readouterr()
        actual = out.splitlines()
        assert sorted(actual) == sorted(expected)
