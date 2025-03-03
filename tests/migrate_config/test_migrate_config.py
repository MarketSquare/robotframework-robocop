import filecmp
import shutil
from difflib import unified_diff
from pathlib import Path

import pytest
from rich.console import Console

from robocop.cli import migrate_config
from robocop.formatter.utils.misc import decorate_diff_with_color

TEST_DATA = Path(__file__).parent / "test_data"


def display_file_diff(expected, actual):
    # TODO: copied over from formatter tests, make common method
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


def test_migrate_config(tmp_path):
    config_path = TEST_DATA / "common.toml"
    expected = TEST_DATA / "common_migrated.toml"
    actual = tmp_path / "common_migrated.toml"
    shutil.copy(config_path, tmp_path)

    migrate_config(tmp_path / "common.toml")

    if not filecmp.cmp(expected, actual):
        display_file_diff(expected, actual)
        pytest.fail(f"File {actual} is not same as expected")
