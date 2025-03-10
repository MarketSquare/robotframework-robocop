from __future__ import annotations

import filecmp
from difflib import unified_diff
from pathlib import Path

import pytest
from packaging import version
from packaging.specifiers import SpecifierSet
from rich.console import Console
from robot.version import VERSION as RF_VERSION

from robocop.cli import format_files
from robocop.formatter.utils.misc import decorate_diff_with_color

VERSION_MATRIX = {"ReplaceReturns": 5, "InlineIf": 5, "ReplaceBreakContinue": 5, "Translate": 6, "ReplaceWithVAR": 7}
ROBOT_VERSION = version.parse(RF_VERSION)


def display_file_diff(expected, actual):
    print("\nExpected file after formatting does not match actual")
    with open(expected, encoding="utf-8") as f, open(actual, encoding="utf-8") as f2:
        expected_lines = f.readlines()
        actual_lines = f2.readlines()
    lines = list(
        unified_diff(expected_lines, actual_lines, fromfile=f"expected: {expected}\t", tofile=f"actual: {actual}\t")
    )
    colorized_output = decorate_diff_with_color(lines)
    console = Console(color_system="windows", width=400)
    for line in colorized_output:
        console.print(line, end="", highlight=False)


class FormatterAcceptanceTest:
    FORMATTER_NAME: str = "PLACEHOLDER"
    FORMATTERS_DIR = Path(__file__).parent / "formatters"

    def compare(
        self,
        source: str,
        not_modified: bool = False,
        expected: str | None = None,
        configure: list[str] = "",
        test_on_version: str | None = None,
        run_all: bool = False,
        select: list[str] | None = None,
        **kwargs,
    ):
        """
        Compare actual (source) and expected files.

        If expected filename is not provided it's assumed to be the same
        as source.
        Use not_modified flag if the content of the file shouldn't be modified by transformer.
        """
        if expected is None:
            expected = source
        if run_all:
            select = []
        else:
            select = [self.FORMATTER_NAME, *select] if select else [self.FORMATTER_NAME]
        self.run_tidy(
            select=select,
            configure=configure,
            source=source,
            not_modified=not_modified,
            test_on_version=test_on_version,
            **kwargs,
        )
        if not not_modified:
            self.compare_file(source, expected)

    def run_tidy(
        self,
        select: list[str] | None = None,
        configure: list[str] | None = None,
        source: str | None = None,
        # exit_code: int = 0, TODO
        not_modified: bool = False,
        test_on_version: str | None = None,
        **kwargs,
    ):
        if not self.enabled_in_version(test_on_version):
            pytest.skip(f"Test enabled only for RF {test_on_version}")
        output_path = self.FORMATTERS_DIR / self.FORMATTER_NAME / "actual" / source
        if source is None:
            source_path = self.FORMATTERS_DIR / self.FORMATTER_NAME / "source"
        else:
            source_path = self.FORMATTERS_DIR / self.FORMATTER_NAME / "source" / source
        format_files(
            sources=[source_path],
            select=select,
            configure=configure,
            overwrite=True,
            check=not_modified,
            output=output_path,
            line_ending="unix",
            **kwargs,
        )
        # if result.exit_code != exit_code:
        #     raise AssertionError(
        #         f"robotidy exit code: {result.exit_code} does not match expected: {exit_code}. "
        #         f"Exception description: {result.exception}"
        #     )
        # return result

    def compare_file(self, actual_name: str, expected_name: str | None = None):
        if expected_name is None:
            expected_name = actual_name
        expected = self.FORMATTERS_DIR / self.FORMATTER_NAME / "expected" / expected_name
        actual = self.FORMATTERS_DIR / self.FORMATTER_NAME / "actual" / actual_name
        if not filecmp.cmp(expected, actual):
            display_file_diff(expected, actual)
            pytest.fail(f"File {actual_name} is not same as expected")

    def enabled_in_version(self, target_version: str | None) -> bool:
        if target_version and ROBOT_VERSION not in SpecifierSet(target_version, prereleases=True):
            return False
        if self.FORMATTER_NAME in VERSION_MATRIX:
            return ROBOT_VERSION.major >= VERSION_MATRIX[self.FORMATTER_NAME]
        return True
