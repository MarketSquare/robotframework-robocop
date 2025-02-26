from __future__ import annotations

import contextlib
import io
import os
import re
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import click.exceptions
import pytest

from robocop.cli import check_files
from robocop.linter.utils.misc import ROBOT_VERSION
from robocop.linter.utils.version_matching import VersionSpecifier

if TYPE_CHECKING:
    from robocop.linter.rules import RuleSeverity


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


@contextlib.contextmanager
def working_directory(path: Path):
    """Change working directory and return to previous on exit"""
    prev_cwd = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(prev_cwd)


def convert_to_output(stdout_bytes):
    return stdout_bytes.decode("utf-8", "replace").replace("\r\n", "\n")


def get_result(encoded_output):
    return convert_to_output(encoded_output.getvalue())


def normalize_result(result, test_data):
    """Remove test data directory path from paths and sort the lines."""
    test_data_str = f"{test_data}{os.path.sep}"
    return sorted([line.replace(test_data_str, "") for line in result])


def load_expected_file(test_data, expected_file):
    if expected_file is None:
        return []
    expected = test_data / expected_file
    with open(expected, encoding="utf-8") as f:
        return sorted(
            [
                re.sub(r"(?<!\\)(?:\\\\)*(\${/})", os.path.sep.replace("\\", "\\\\"), line.rstrip("\n")).replace(
                    "\\${/}", "${/}"
                )
                for line in f
            ]
        )


class RuleAcceptance:
    SRC_FILE = "."
    EXPECTED_OUTPUT = "expected_output.txt"
    DEFAULT_ISSUE_FORMAT = "{source}:{line}:{col} [{severity}] {rule_id} {desc}"
    END_COL_ISSUE_FORMAT = "{source}:{line}:{col}:{end_line}:{end_col} [{severity}] {rule_id} {desc}"

    def check_rule(
        self,
        expected_file: str | None = None,
        configure: list[str] | None = None,
        threshold: RuleSeverity | None = None,
        select: list[str] | None = None,
        src_files: list | None = None,
        test_on_version: str | list[str] | None = None,
        issue_format: str = "default",
        language: list[str] | None = None,
        # deprecated: bool = False, TODO
        **kwargs,
    ):
        if not self.enabled_in_version(test_on_version):
            pytest.skip(f"Test enabled only for RF {test_on_version}")
        test_data = self.test_class_dir
        expected = load_expected_file(test_data, expected_file)
        issue_format = self.get_issue_format(issue_format)
        if select is None:
            select = [self.rule_name]
        if src_files is None:
            paths = [test_data]
        else:
            paths = [test_data / src_file for src_file in src_files]
        with isolated_output() as output, working_directory(test_data):
            try:
                with pytest.raises(click.exceptions.Exit):
                    check_files(
                        sources=paths,
                        select=select,
                        configure=configure,
                        issue_format=issue_format,
                        threshold=threshold,
                        language=language,
                        **kwargs,
                    )
            finally:
                sys.stdout.flush()
                result = get_result(output)
                parsed_results = result.splitlines()
        actual = normalize_result(parsed_results, test_data)
        # if deprecated:  # TODO:
        #     assert runner.rules[self.rule_name].deprecation_warning in actual
        # elif
        if actual != expected:
            missing_expected = sorted(set(actual) - set(expected))
            missing_actual = sorted(set(expected) - set(actual))
            error = "Actual issues are different than expected.\n"
            if missing_expected:
                present_in_actual = "\n    ".join(missing_expected)
                error += f"Actual issues not found in expected:\n    {present_in_actual}\n\n"
            if missing_actual:
                present_in_expected = "\n    ".join(missing_actual)
                error += f"Expected issues not found in actual:\n    {present_in_expected}"
            pytest.fail(error, pytrace=False)

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
    def enabled_in_version(test_on_version: list | str | None):
        """
        Check if rule is enabled for given target version condition.

        If the target version condition is a string it needs to match with RF version.
        If target version is a string and  contains `;`, the string is split into list and each element is a condition
        that should match RF version.
        If the target version is a list of strings, any version conditions need to match.
        """
        if test_on_version is None:
            return True
        if isinstance(test_on_version, list):
            return any(ROBOT_VERSION in VersionSpecifier(version) for version in test_on_version)
        if ";" in test_on_version:
            must_match_versions = test_on_version.split(";")
            return all(ROBOT_VERSION in VersionSpecifier(version) for version in must_match_versions)
        return ROBOT_VERSION in VersionSpecifier(test_on_version)
