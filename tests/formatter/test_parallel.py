import shutil
from pathlib import Path

import pytest

from robocop import parallel
from robocop.run import format_files
from tests import working_directory

SUITE = """\
*** Keywords ***
Keyword {index}
  [Arguments]  ${{arg}}
  ${{value}}=  Set Variable  {index}
  IF  $arg
    Log  ${{value}}
  END


*** Test Cases ***
Test {index}
    Keyword {index}    1
"""


@pytest.fixture(autouse=True)
def one_file_per_worker(monkeypatch):
    monkeypatch.setattr(parallel, "MIN_FILES_PER_WORKER", 1)


def create_project(path: Path) -> None:
    for index in range(12):
        directory = path / f"dir{index % 3}"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / f"suite{index}.robot").write_text(SUITE.format(index=index))
    (path / "dir2" / "formatted.robot").write_text("*** Test Cases ***\nTest\n    No Operation\n")
    (path / "dir1" / "robocop.toml").write_text("[format]\nspace_count = 2\n")


def read_files(root: Path) -> dict[str, str]:
    return {path.relative_to(root).as_posix(): path.read_text() for path in sorted(root.rglob("*.robot"))}


@pytest.mark.parametrize("overwrite", [True, False])
def test_parallel_formatting_matches_serial(tmp_path, capsys, overwrite):
    # directories with names of the same length, so that the tabs in the diff are expanded in the same way
    serial_root, parallel_root = tmp_path / "jobs_1", tmp_path / "jobs_3"
    create_project(serial_root)
    shutil.copytree(serial_root, parallel_root)
    with working_directory(serial_root):
        serial_code = format_files(overwrite=overwrite, diff=True, color=False, return_result=True, jobs=1)
    serial_output = capsys.readouterr().out.replace(str(serial_root), "<root>")
    with working_directory(parallel_root):
        parallel_code = format_files(overwrite=overwrite, diff=True, color=False, return_result=True, jobs=3)
    parallel_output = capsys.readouterr().out.replace(str(parallel_root), "<root>")

    assert serial_code == parallel_code
    assert "12 files would be reformatted" in serial_output or "12 files reformatted" in serial_output
    assert serial_output == parallel_output
    serial_files = read_files(serial_root)
    assert serial_files == read_files(parallel_root)
    assert (serial_files["dir0/suite0.robot"] != SUITE.format(index=0)) is overwrite
    if overwrite:
        assert "\n  Keyword 1  1\n" in serial_files["dir1/suite1.robot"]
