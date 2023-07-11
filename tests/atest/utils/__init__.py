import contextlib
import io
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

import pytest

from robocop import Robocop
from robocop.config import Config
from robocop.utils.misc import ROBOT_VERSION
from robocop.utils.version_matching import VersionSpecifier


@contextlib.contextmanager
def isolated_output():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    bytes_output = io.BytesIO()
    sys.stdout = io.TextIOWrapper(bytes_output, encoding="utf-8")
    sys.stderr = sys.stdout
    yield bytes_output
    sys.stdout = old_stdout
    sys.stderr = old_stderr


def convert_to_output(stdout_bytes):
    return stdout_bytes.decode("utf-8", "replace").replace("\r\n", "\n")


def get_result(encoded_output):
    stdout = convert_to_output(encoded_output.getvalue())
    return stdout


def normalize_result(result, test_data):
    """Remove test data directory path from paths and sort the lines."""
    test_data_str = f"{test_data}{os.path.sep}"
    return sorted([line.replace(test_data_str, "") for line in result])


def remove_deprecation_warning(result):
    """Remove deprecation warning from the results"""
    deprecation_regex = (
        r"(?s)(\#\#\# DEPRECATION WARNING \#\#\#)(.*?)(This information will disappear in the next version\.\n+)"
    )
    return re.sub(deprecation_regex, "", result)


def load_expected_file(test_data, expected_file):
    if expected_file is None:
        return []
    expected = test_data / expected_file
    with open(expected, encoding="utf-8") as f:
        return sorted([line.rstrip("\n").replace(r"${/}", os.path.sep) for line in f])


def configure_robocop_with_rule(args, runner, rule, path, src_files: Optional[List], format):
    runner.from_cli = True
    config = Config()
    if src_files is None:
        paths = [str(path)]
    else:
        paths = [str(path / src_file) for src_file in src_files]
    if args is None:
        args = []
    elif isinstance(args, str):
        args = args.split()
    arguments = ["--include", ",".join(rule)]
    arguments.extend(
        [
            "--format",
            format,
            "--configure",
            "return_status:quality_gate:E=0:W=0:I=0",
            *args,
            *paths,
        ]
    )
    config.parse_args(arguments)
    runner.config = config
    return runner


class RuleAcceptance:
    SRC_FILE = "."
    EXPECTED_OUTPUT = "expected_output.txt"
    DEFAULT_ISSUE_FORMAT = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
    END_COL_ISSUE_FORMAT = "{source}:{line}:{col}:{end_line}:{end_col} [{severity}] {rule_id} {desc}"

    def check_rule(
        self,
        expected_file,
        config=None,
        rule=None,
        src_files: Optional[List] = None,
        target_version=None,
        issue_format="default",
    ):
        if not self.enabled_in_version(target_version):
            pytest.skip(f"Test enabled only for RF {target_version}")
        test_data = self.test_class_dir
        expected = load_expected_file(test_data, expected_file)
        format = self.get_issue_format(issue_format)
        if rule is None:
            rule = [self.rule_name]
        robocop_instance = configure_robocop_with_rule(config, Robocop(), rule, test_data, src_files, format=format)
        with isolated_output() as output, pytest.raises(SystemExit):
            try:
                robocop_instance.run()
            finally:
                sys.stdout.flush()
                result = get_result(output)
                parsed_results = remove_deprecation_warning(result).splitlines()
        actual = normalize_result(parsed_results, test_data)
        if actual != expected:
            missing_expected = sorted(set(actual) - set(expected))
            missing_actual = sorted(set(expected) - set(actual))
            present_in_actual = "\n    ".join(missing_expected)
            present_in_expected = "\n    ".join(missing_actual)
            raise AssertionError(
                "Actual issues are different than expected.\n"
                f"Actual issues not found in expected:\n    {present_in_actual}"
                f"\n\nExpected issues not found in actual:\n    {present_in_expected}"
            )
        assert actual == expected, f"{actual} != {expected}"

    def get_issue_format(self, issue_format):
        if issue_format == "default":
            return self.DEFAULT_ISSUE_FORMAT
        if issue_format == "end_col":
            return self.END_COL_ISSUE_FORMAT
        return issue_format

    @property
    def test_class_dir(self):
        return Path(sys.modules[self.__class__.__module__].__file__).parent

    @property
    def rule_name(self):
        return self.test_class_dir.stem.replace("_", "-")

    def rule_is_enabled(self, robocop_rules):
        return robocop_rules[self.rule_name].enabled_in_version

    @staticmethod
    def enabled_in_version(target_version):
        if target_version is None:
            return True
        if isinstance(target_version, list):
            return any(ROBOT_VERSION in VersionSpecifier(version) for version in target_version)
        return ROBOT_VERSION in VersionSpecifier(target_version)
