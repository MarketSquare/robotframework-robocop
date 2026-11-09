from pathlib import Path

import pytest

from robocop.files import get_relative_path

ROOT = Path.cwd().anchor


@pytest.mark.parametrize(
    ("path", "parent", "expected"),
    [
        (Path(ROOT, "project", "dir", "file.robot"), Path(ROOT, "project"), Path("dir", "file.robot")),
        (str(Path(ROOT, "project", "file.robot")), Path(ROOT, "project"), Path("file.robot")),
        (Path(ROOT, "project"), Path(ROOT, "project"), Path()),
        (Path(ROOT, "project", "file.robot"), Path(ROOT), Path("project", "file.robot")),
        (Path(ROOT, "project2", "file.robot"), Path(ROOT, "project"), Path(ROOT, "project2", "file.robot")),
        (Path(ROOT, "other", "file.robot"), Path(ROOT, "project"), Path(ROOT, "other", "file.robot")),
        (Path("dir", "file.robot"), Path(), Path("dir", "file.robot")),
    ],
)
def test_get_relative_path(path, parent, expected):
    assert get_relative_path(path, parent) == expected
