import os
import sys
from pathlib import Path

import pytest

from robocop import Robocop
from robocop.config import Config


def load_expected_file(test_data, expected_file):
    expected = test_data / expected_file
    with open(expected, encoding="utf-8") as f:
        return sorted([line.rstrip("\n") for line in f])


def load_actual_results(capsys, test_data):
    out, _ = capsys.readouterr()
    actual = out.splitlines()
    test_data_str = f"{test_data}{os.path.sep}"
    return sorted([line.replace(test_data_str, "") for line in actual])


def configure_robocop_with_rule(args, runner, rule, path, src_files):
    runner.from_cli = True
    config = Config()
    if src_files is None:
        paths = [str(path)]
    else:
        paths = [str(path / src_file) for src_file in src_files]
    arguments = ["--include", ",".join(rule)]
    arguments.extend(
        [
            "--format",
            "{source}:{line}:{col} [{severity}] {rule_id} {desc}",
            "--configure",
            "return_status:quality_gate:E=0:W=0:I=0",
            *args,
            *paths,
        ]
    )
    config.parse_opts(arguments)
    runner.config = config
    return runner


class RuleAcceptance:
    SRC_FILE = "."
    EXPECTED_OUTPUT = "expected_output.txt"

    def check_rule(self, capsys, expected_file, config=None, rule=None, src_files=None):
        test_data = self.test_class_dir
        expected = load_expected_file(test_data, expected_file)
        if rule is None:
            rule = [self.rule_name]
        if config is None:
            config = []
        else:
            config = config.split()
        robocop_instance = Robocop(from_cli=False)
        robocop_instance = configure_robocop_with_rule(config, robocop_instance, rule, test_data, src_files)
        with pytest.raises(SystemExit):
            robocop_instance.run()
        actual = load_actual_results(capsys, test_data)
        assert actual == expected

    @property
    def test_class_dir(self):
        return Path(sys.modules[self.__class__.__module__].__file__).parent

    @property
    def rule_name(self):
        return self.test_class_dir.stem.replace("_", "-")

    def rule_is_enabled(self, robocop_rules):
        return robocop_rules[self.rule_name].enabled_in_version
