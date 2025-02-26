import json
from pathlib import Path

import platformdirs
import pytest

import robocop.linter.exceptions
from robocop.linter.reports import (
    ROBOCOP_CACHE_FILE,
    get_reports,
    load_reports_result_from_cache,
    save_reports_result_to_cache,
)


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (["timestamp", "sarif"], ["print_issues", "timestamp", "sarif"]),
        (["timestamp"], ["print_issues", "timestamp"]),
        (["version", "timestamp", "version"], ["print_issues", "version", "timestamp"]),
    ],
)
def test_get_reports(configured, expected, config):
    config.linter.reports = configured
    reports = get_reports(config)
    assert list(reports.keys()) == expected


def test_get_reports_all(config):
    config.linter.reports = ["all"]
    reports = get_reports(config)
    assert "timestamp" in reports
    assert "sarif" not in reports
    config.linter.reports = ["all", "sarif"]
    reports = get_reports(config)
    assert "timestamp" in reports
    assert "sarif" in reports
    # Check order with all
    config.linter.reports = ["version", "all", "sarif"]
    reports = get_reports(config)
    reports_list = list(reports.keys())
    assert reports_list.index("version") < reports_list.index("timestamp") < reports_list.index("sarif")


def test_get_unknown_report(config):
    config.linter.reports = ["all", "unknown"]
    with pytest.raises(robocop.linter.exceptions.InvalidReportName, match="Provided report 'unknown' does not exist."):
        get_reports(config)


def clear_cache():
    cache_file = Path(platformdirs.user_cache_dir("robocop", ensure_exists=True)) / ROBOCOP_CACHE_FILE
    with open(cache_file, "w") as fp:
        json_string = json.dumps({}, indent=4)
        fp.write(json_string)


def remove_cache_file():
    cache_file = Path(platformdirs.user_cache_dir("robocop")) / ROBOCOP_CACHE_FILE
    if cache_file.is_file():
        cache_file.unlink()


def save_invalid_cache_file():
    cache_file = Path(platformdirs.user_cache_dir("robocop", ensure_exists=True)) / ROBOCOP_CACHE_FILE
    with open(cache_file, "w") as fp:
        fp.write("")


def test_save_load_result_from_cache():
    clear_cache()
    # Write new
    root_1 = "C://path/to/dir"
    root_1_content = {"time_taken": "2.000"}
    expected_result = {root_1: root_1_content}
    save_reports_result_to_cache(root_1, root_1_content)
    result = load_reports_result_from_cache()
    assert result == expected_result
    # Write but different root
    root_2 = "D://robot_tests/"
    root_2_content = {
        "version": {"generated_with": "3.2.1"},
        "rules_by_id": {"I0913 (can-be-resource-file)": 1, "W0919 (unused-argument)": 1},
    }
    expected_result = {root_1: root_1_content, root_2: root_2_content}
    save_reports_result_to_cache(root_2, root_2_content)
    result = load_reports_result_from_cache()
    assert result == expected_result
    # Overwrite first root
    root_2_new_content = {"time_taken": "3.000"}
    expected_result = {root_1: root_1_content, root_2: root_2_new_content}
    save_reports_result_to_cache(root_2, root_2_new_content)
    result = load_reports_result_from_cache()
    assert result == expected_result


@pytest.mark.parametrize("prepare_file_fn", [remove_cache_file, save_invalid_cache_file])
def test_load_save_with_invalid_file(prepare_file_fn):
    prepare_file_fn()
    result = load_reports_result_from_cache()
    assert result is None
    root_1 = "C://path/to/dir"
    root_1_content = {"time_taken": "2.000"}
    expected_result = {root_1: root_1_content}
    save_reports_result_to_cache(root_1, root_1_content)
    result = load_reports_result_from_cache()
    assert result == expected_result
