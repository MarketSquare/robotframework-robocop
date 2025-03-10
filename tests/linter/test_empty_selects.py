from pathlib import Path

import pytest

from robocop.cli import check_files
from robocop.linter.rules import RuleSeverity
from tests import working_directory

TEST_DIR = Path(__file__).parent / "test_data" / "example_test"


def test_no_files_selected(tmp_path, capsys):
    with working_directory(tmp_path):
        ret = check_files(ignore_file_config=True, return_result=True)
    out, _ = capsys.readouterr()
    expected = "No Robot files were found with the existing configuration.\n"
    assert not ret
    assert out == expected


@pytest.mark.parametrize(
    "config",
    [
        {"select": ["X"]},  # select non-existing rule only
        {"select": ["could-be-test-tags"], "threshold": RuleSeverity.ERROR},  # rule is info, so it will be filtered
        {"select": ["could-be-test-tags"], "ignore": ["could-be-test-tags"]},  # select and ignore the same rule
        {"select": ["replace-set-variable-with-var"], "target_version": 4},  # rule available from 7
    ],
)
def test_select_empty_rule_set_from_cli(config, capsys):
    with working_directory(TEST_DIR):
        ret = check_files(**config, ignore_file_config=True, return_result=True)
    out, _ = capsys.readouterr()
    expected = (
        "No rule selected with the existing configuration from the cli . "
        "Please check if all rules from --select exist and there is no conflicting filter option.\n"
    )
    assert not ret
    assert out == expected


def test_select_empty_rule_set_from_config_file(capsys):
    with working_directory(TEST_DIR):
        ret = check_files(ignore_file_config=False, return_result=True)
    out, _ = capsys.readouterr()
    expected = (
        f"No rule selected with the existing configuration from the {TEST_DIR / 'pyproject.toml'} . "
        "Please check if all rules from --select exist and there is no conflicting filter option.\n"
    )
    assert not ret
    assert out == expected
