import os
from pathlib import Path

import pytest
import yaml

from robocop.checkers import get_rules
from robocop.config import Config
from robocop.utils import ROBOT_VERSION


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
    with open(expected_file, encoding="utf-8") as f:
        return [replace_paths(line, str(src)) for line in f]


def get_covered_threshold_severity_tests():
    is_covered = set()

    with open(Path(__file__).parent / "custom_tests.yaml") as f:
        tests = yaml.safe_load(f)
    for rule, configs in tests["tests"].items():
        for config in configs:
            test_config = config["config"]
            if not test_config:
                continue
            if isinstance(test_config, str):
                if "severity_threshold" in test_config:
                    is_covered.add(rule)
            else:
                for conf in test_config:
                    if "severity_threshold" in conf:
                        is_covered.add(rule)
    return is_covered


def test_threshold_severity_coverage():
    require_coverage = set()
    for _, rule in get_rules():
        if rule.config.get("severity_threshold", None):
            require_coverage.add(rule.name)

    is_covered = get_covered_threshold_severity_tests()
    covered = require_coverage - is_covered
    assert covered == set(), "There are rules with severity_threshold not covered by tests"


def test_rule(rule, args, test_data, enabled, robocop_instance, capsys):
    args = args if args is not None else []
    src, expected_file = find_test_data(test_data, rule)
    expected = load_expected_file(expected_file, src)
    robocop_instance = configure_robocop_with_rule(args, robocop_instance, rule, src)
    with pytest.raises(SystemExit) as system_exit:
        robocop_instance.run()
    if not enabled:
        assert system_exit.value.code == 0
    else:
        out, _ = capsys.readouterr()
        actual = out.splitlines()
        assert sorted(actual) == sorted(expected)
