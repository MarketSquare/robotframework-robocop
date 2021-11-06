import os
from pathlib import Path

import pytest
from packaging.specifiers import SpecifierSet

from robocop.config import Config
from robocop.utils import ROBOT_VERSION

# if rule was enabled/disabled for particular RF version, add it there
support_matrix = {
    "nested-for-loop": SpecifierSet("~=3.0"),
    "invalid-comment": SpecifierSet("~=3.0"),
    "if-can-be-used": SpecifierSet(">=4.0"),
    "else-not-upper-case": SpecifierSet(">=4.0"),
    "variable-should-be-left-aligned": SpecifierSet(">=4.0"),
    "invalid-argument": SpecifierSet(">=4.0"),
    "invalid-if": SpecifierSet(">=4.0"),
    "invalid-for-loop": SpecifierSet(">=4.0"),
    "not-enough-whitespace-after-variable": SpecifierSet(">=4.0"),
    "suite-setting-should-be-left-aligned": SpecifierSet(">=4.0"),
    "if-can-be-merged": SpecifierSet(">=4.0")
}


def configure_robocop_with_rule(args, runner, rule, path):
    runner.from_cli = True
    config = Config()
    config.parse_opts(
        [
            "--include",
            rule,
            "--format",
            "{source}:{line}:{col} [{severity}] {rule_id} {desc}",
            "--configure",
            "return_status:quality_gate:E=0:W=0:I=0",
            *args,
            str(path),
        ]
    )
    runner.config = config
    return runner


def replace_paths(line, rules_dir):
    return line.replace("${rules_dir}", rules_dir).replace(r"${\}", os.path.sep).rstrip("\n")


def find_test_data(test_data_path, rule):
    current_dir = Path(__file__).parent
    test_data = Path(current_dir, "rules", test_data_path)
    expected_output = Path(test_data, f"expected_output_rf{ROBOT_VERSION.major}.txt")
    if not expected_output.exists():
        expected_output = Path(test_data, "expected_output.txt")
    assert test_data.exists(), f"Missing test data for rule '{rule}'"
    assert expected_output.exists(), f"Missing expected_output.txt file for rule '{rule}'"
    return test_data, expected_output


def load_expected_file(expected_file, src):
    with open(expected_file) as f:
        return [replace_paths(line, str(src)) for line in f]


def test_rule(rule, args, test_data, robocop_instance, capsys):
    args = args if args is not None else []
    src, expected_file = find_test_data(test_data, rule)
    expected = load_expected_file(expected_file, src)
    robocop_instance = configure_robocop_with_rule(args, robocop_instance, rule, src)
    with pytest.raises(SystemExit) as system_exit:
        robocop_instance.run()
    if rule in support_matrix and ROBOT_VERSION not in support_matrix[rule]:
        assert system_exit.value.code == 0
    else:
        out, _ = capsys.readouterr()
        actual = out.splitlines()
        assert sorted(actual) == sorted(expected)
