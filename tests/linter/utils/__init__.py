from __future__ import annotations

import contextlib
import filecmp
import io
import os
import re
import shutil
import sys
from difflib import unified_diff
from pathlib import Path
from typing import TYPE_CHECKING
from unittest import mock

import click.exceptions
import pytest
from rich.console import Console

from robocop.run import check_files, check_project
from robocop.version_handling import ROBOT_VERSION, VersionSpecifier
from tests import working_directory
from tests.formatter import display_file_diff

if TYPE_CHECKING:
    from robocop.linter.rules import RuleSeverity


@contextlib.contextmanager
def isolated_output():
    old_stdout = sys.stdout
    old_stderr = sys.stderr
    bytes_output = io.BytesIO()
    sys.stdout = io.TextIOWrapper(bytes_output, encoding="utf-8")
    sys.stderr = sys.stdout
    # By default, pytest uses 80-chars long terminal which depends on COLUMNS env variable
    with mock.patch.dict(os.environ, {"COLUMNS": "200"}, clear=True):
        yield bytes_output
    sys.stdout = old_stdout
    sys.stderr = old_stderr


def convert_to_output(stdout_bytes):
    return stdout_bytes.decode("utf-8", "replace").replace("\r\n", "\n")


def get_result(encoded_output):
    return convert_to_output(encoded_output.getvalue())


def normalize_result(result, test_data, sort_lines: bool):
    """Remove test data directory path from paths and sort the lines."""
    test_data_str = f"{test_data}{os.path.sep}"
    lines = [line.replace(test_data_str, "") for line in result]
    if sort_lines:
        return sorted(lines)
    return lines


def load_expected_file(test_data, expected_file, sort_lines: bool):
    if expected_file is None:
        return ["", "No issues found."]
    if expected_file == "not_enabled":
        return [
            "No rule selected with the existing configuration from the cli . "
            "Please check if all rules from --select exist and there is no conflicting filter option.",
            "No issues found.",
            "",
        ]
    expected = test_data / expected_file
    with open(expected, encoding="utf-8") as f:
        lines = [
            re.sub(r"(?<!\\)(?:\\\\)*(\${/})", os.path.sep.replace("\\", "\\\\"), line.rstrip("\n")).replace(
                "\\${/}", "${/}"
            )
            for line in f
        ]
        if sort_lines:
            return sorted(lines)
        return lines


def display_lines_diff(expected: list[str], actual: list[str]):
    lines = list(unified_diff(expected, actual, fromfile="expected:\t", tofile="actual:\t"))
    # colorized_output = decorate_diff_with_color(lines)
    console = Console(color_system="auto", width=400)
    for line in lines:
        console.print(line, highlight=False)


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
        output_format: str = "simple",
        deprecated: bool = False,
        exit_code: int | None = None,
        compare_output: bool = True,
        test_dir: Path | None = None,
        project_check: bool = False,
        **kwargs: object,
    ) -> str | None:
        if not self.enabled_in_version(test_on_version):
            pytest.skip(f"Test enabled only for RF {test_on_version}")
        if project_check:
            test_fn = check_project
        else:
            test_fn = check_files
            kwargs["cache"] = False
        test_data = test_dir or self.test_class_dir
        sort_lines = output_format == "simple"
        issue_format = self.get_issue_format(issue_format)
        if select is None:
            select = [self.rule_name]
        if src_files is None:
            paths = [test_data]
        else:
            paths = [test_data / src_file for src_file in src_files]
        if configure is None:
            configure = []
        configure.append(f"print_issues.output_format={output_format}")
        with isolated_output() as output, working_directory(test_data):
            try:
                with pytest.raises(click.exceptions.Exit) as exc_info:
                    test_fn(
                        sources=paths,
                        select=select,
                        configure=configure,
                        issue_format=issue_format,
                        threshold=threshold,
                        language=language,
                        ignore_file_config=True,
                        **kwargs,
                    )
            finally:
                sys.stdout.flush()
                result = get_result(output)
        if exit_code is not None:
            assert exc_info.value.exit_code == exit_code
        if not compare_output:
            return result
        self._compare_output(result, expected_file, test_data, sort_lines, deprecated)
        return None

    def check_rule_fix(
        self,
        src_files: list[str],
        expected_dir: str = "expected_fixed",
        configure: list[str] | None = None,
        threshold: RuleSeverity | None = None,
        select: list[str] | None = None,
        test_on_version: str | list[str] | None = None,
        language: list[str] | None = None,
        test_dir: Path | None = None,
        **kwargs: object,
    ):
        """
        Test rule fixes by applying them to source files and comparing with expected output.

        Args:
            src_files: List of source files to fix. If None, uses all files in the test directory.
            expected_dir: Directory name containing expected fixed files (relative to test directory).
            configure: Additional configuration options.
            threshold: Severity threshold.
            select: Rules to select (defaults to current rule).
            test_on_version: RF version requirement.
            language: Language configuration.
            test_dir: Test directory (defaults to test class directory).
            **kwargs: Additional arguments passed to check_files.

        """
        if not self.enabled_in_version(test_on_version):
            pytest.skip(f"Test enabled only for RF {test_on_version}")

        test_data = test_dir or self.test_class_dir
        expected_path = test_data / expected_dir
        actual_path = test_data / "actual_fixed"

        # Clean up actual directory if it exists
        if actual_path.exists():
            shutil.rmtree(actual_path)
        actual_path.mkdir(parents=True, exist_ok=True)

        if select is None:
            select = [self.rule_name]

        paths = [test_data / src_file for src_file in src_files]
        for src_file in paths:
            shutil.copy2(src_file, actual_path)
        paths = [actual_path / src_file for src_file in src_files]

        with isolated_output() as output, working_directory(test_data):
            try:
                with pytest.raises(click.exceptions.Exit):
                    check_files(
                        sources=paths,
                        select=select,
                        configure=configure,
                        threshold=threshold,
                        language=language,
                        ignore_file_config=True,
                        fix=True,
                        cache=False,
                        **kwargs,
                    )
            finally:
                sys.stdout.flush()
                result = get_result(output)

        # Compare console output (fix summary and other output)
        self._compare_output(result, expected_path / "expected_output.txt", test_data, sort_lines=False)

        if not kwargs.get("diff", False):
            for src_file in src_files:
                self._compare_fixed_file(src_file, expected_path, actual_path)

    def _compare_output(
        self, result: str, expected_file: Path | str | None, test_data: Path, sort_lines: bool, deprecated: bool = False
    ):
        """Compare actual output with expected output."""
        parsed_results = result.splitlines()
        expected = load_expected_file(test_data, expected_file, sort_lines=sort_lines)
        actual = normalize_result(parsed_results, test_data, sort_lines=sort_lines)
        if deprecated:
            assert actual
            assert "No rule selected" in actual[-1]
            return
        if actual != expected:
            error = "Actual issues are different than expected.\n"
            if sort_lines:
                missing_expected = sorted(set(actual) - set(expected))
                missing_actual = sorted(set(expected) - set(actual))
                if missing_expected:
                    present_in_actual = "\n    ".join(missing_expected)
                    error += f"Actual issues not found in expected:\n    {present_in_actual}\n\n"
                if missing_actual:
                    present_in_expected = "\n    ".join(missing_actual)
                    error += f"Expected issues not found in actual:\n    {present_in_expected}"
                if not (missing_expected or missing_actual):
                    return
            else:
                # false alarm (rare occurrence if OS have random file order), we don't sort at first to save time
                if sorted(actual) == sorted(expected):
                    return
                display_lines_diff(expected, actual)
            pytest.fail(error, pytrace=False)

    def _compare_fixed_file(self, filename: str, expected_dir: Path, actual_dir: Path):
        """Compare a single fixed file with the expected output."""
        expected_file = expected_dir / filename
        actual_file = actual_dir / filename

        if not expected_file.exists():
            pytest.fail(f"Expected file not found: {expected_file}")

        if not actual_file.exists():
            pytest.fail(f"Actual file not found: {actual_file}")

        if not filecmp.cmp(expected_file, actual_file) and display_file_diff(expected_file, actual_file):
            pytest.fail(f"Fixed file {filename} does not match expected output")

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
        Check if the rule is enabled for the given target version condition.

        If the target version condition is a string, it needs to match with the RF version.
        If the target version is a string and contains, `;`, the string is split into the list
        and each element is a condition that should match the RF version.
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
