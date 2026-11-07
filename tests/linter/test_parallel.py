import shutil
from pathlib import Path

import pytest

from robocop import parallel
from robocop.config.builder import ConfigBuilder
from robocop.config.schema import RawConfig
from robocop.exceptions import ConfigurationError
from robocop.run import check_files
from tests import working_directory

SUITE = """\
*** Settings ***
Documentation    Suite {index}.

*** Test Cases ***
Test {index}
    [Tags]    tag{index}
    Keyword {index}    ${{arg}}
    Log  single space separator
    IF    $condition
        No Operation
    END

*** Keywords ***
Keyword {index}
    [Arguments]    ${{arg}}
    ${{unused}}    Set Variable    {index}
    Log    ${{arg}}
"""


@pytest.fixture(autouse=True)
def one_file_per_worker(monkeypatch):
    monkeypatch.setattr(parallel, "MIN_FILES_PER_WORKER", 1)


def create_project(path: Path) -> None:
    for index in range(12):
        directory = path / f"dir{index % 3}" / f"sub{index % 2}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"suite{index}.robot").write_text(SUITE.format(index=index))
    (path / "pyproject.toml").write_text('[tool.robocop.lint]\nconfigure = ["unused-variable.severity=E"]\n')
    (path / "dir1" / "robocop.toml").write_text('extends = ["../pyproject.toml"]\n[lint]\nignore = ["DOC01"]\n')


def diagnostics_summary(diagnostics, root: Path) -> list[tuple]:
    return [
        (
            diag.source.path.relative_to(root).as_posix(),
            diag.rule.rule_id,
            diag.range.start.line,
            diag.range.start.character,
            diag.range.end.line,
            diag.range.end.character,
            diag.severity,
            diag.message,
        )
        for diag in diagnostics
    ]


def test_parallel_results_match_serial(tmp_path):
    create_project(tmp_path)
    with working_directory(tmp_path):
        serial = diagnostics_summary(check_files(return_result=True, silent=True, cache=False, jobs=1), tmp_path)
        cold = diagnostics_summary(check_files(return_result=True, silent=True, jobs=3), tmp_path)
        warm = diagnostics_summary(check_files(return_result=True, silent=True, jobs=3), tmp_path)

    assert serial
    assert any(rule_id == "DOC01" for _, rule_id, *_ in serial)
    assert not any(rule_id == "DOC01" and path.startswith("dir1/") for path, rule_id, *_ in serial)
    assert any(rule_id == "VAR02" and severity.value == "E" for _, rule_id, *_, severity, _ in serial)
    assert serial == cold
    assert serial == warm


def test_parallel_fix_matches_serial(tmp_path):
    serial_root, parallel_root = tmp_path / "serial", tmp_path / "parallel"
    create_project(serial_root)
    shutil.copytree(serial_root, parallel_root)
    with working_directory(serial_root):
        diagnostics = check_files(return_result=True, silent=True, cache=False, fix=True, jobs=1)
        serial = diagnostics_summary(diagnostics, serial_root)
    with working_directory(parallel_root):
        diagnostics = check_files(return_result=True, silent=True, cache=False, fix=True, jobs=3)
        in_parallel = diagnostics_summary(diagnostics, parallel_root)

    assert serial == in_parallel
    serial_files = sorted(serial_root.rglob("*.robot"))
    assert serial_files
    for serial_file in serial_files:
        parallel_file = parallel_root / serial_file.relative_to(serial_root)
        assert serial_file.read_text() == parallel_file.read_text()
    assert serial_file.read_text() != SUITE.format(index=11)


@pytest.mark.parametrize("jobs", [-1, "2", True])
def test_invalid_jobs_in_configuration_file(jobs):
    with pytest.raises(ConfigurationError, match="jobs"):
        ConfigBuilder().jobs_from_raw(RawConfig(jobs=jobs), None)
