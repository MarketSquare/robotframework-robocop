import filecmp
import shutil
from difflib import unified_diff
from pathlib import Path

import pytest
from rich.console import Console

from robocop.formatter.utils.misc import decorate_diff_with_color
from robocop.run import migrate_config

TEST_DATA = Path(__file__).parent / "test_data"


def display_file_diff(expected, actual) -> bool:
    """
    Display difference between files.

    If files are only different with EOLs, return False. Return True otherwise.
    """
    # TODO: copied over from formatter tests, make common method
    print("\nExpected file after formatting does not match actual")
    with open(expected, encoding="utf-8") as f, open(actual, encoding="utf-8") as f2:
        expected_lines = f.readlines()
        actual_lines = [line.replace("\r\n", "\n") for line in f2]
    lines = list(
        unified_diff(expected_lines, actual_lines, fromfile=f"expected: {expected}\t", tofile=f"actual: {actual}\t")
    )
    if not lines:
        return False
    colorized_output = decorate_diff_with_color(lines)
    console = Console(color_system="windows", width=400)
    for line in colorized_output:
        console.print(line, end="", highlight=False)
    return True


@pytest.mark.parametrize(
    ("source_config", "expected_config"),
    [
        ("common", "common_migrated.toml"),
        ("common_hyphens", "common_migrated.toml"),
        ("skip", "skip_migrated.toml"),
        ("skip_false", None),
    ],
)
def test_migrate_config(source_config, expected_config, tmp_path):
    config_path = TEST_DATA / f"{source_config}.toml"
    if expected_config is None:
        expected = None
    else:
        expected = TEST_DATA / expected_config
    actual = tmp_path / f"{source_config}_migrated.toml"
    shutil.copy(config_path, tmp_path)

    migrate_config(tmp_path / f"{source_config}.toml")
    if not expected:
        assert not actual.exists()
    elif not filecmp.cmp(expected, actual):
        if not display_file_diff(expected, actual):
            return
        pytest.fail(f"File {actual} is not same as expected")
