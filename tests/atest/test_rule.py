import pytest
from pathlib import Path
from robocop.config import Config


def configure_robocop_with_rule(runner, rule, path):
    config = Config()
    config.parse_opts([
        '--include',
        rule,
        '--format',
        '{rel_source}:{line}:{col} [{severity}] {rule_id} {desc}',
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


def test_rule(rule, robocop_instance, capsys):
    test_data = Path('rules', rule)
    expected_output = Path('rules', rule, 'expected_output.txt')
    assert test_data.exists(), f"Missing test data for rule '{rule}'"
    assert expected_output.exists(), f"Missing expected_output.txt file for rule '{rule}'"
    with open(expected_output) as f:
        expected = f.readlines()
    expected = [line.strip('\n') for line in expected]
    robocop_instance = configure_robocop_with_rule(robocop_instance, rule, test_data)
    with pytest.raises(SystemExit) as system_exit:
        robocop_instance.run()
    assert system_exit.value.code > 0
    out, _ = capsys.readouterr()
    actual = out.splitlines()
    assert actual == expected
