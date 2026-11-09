from pathlib import Path

import pytest

from robocop import files
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


@pytest.fixture
def clear_resolved_paths(monkeypatch):
    monkeypatch.setattr(files, "_resolved_paths", {})


@pytest.mark.usefixtures("clear_resolved_paths")
def test_resolve_path_follows_symlinked_file(tmp_path):
    target = tmp_path / "target" / "file.robot"
    target.parent.mkdir()
    target.touch()
    link = tmp_path / "links" / "link.robot"
    link.parent.mkdir()
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("Symlinks are not supported")
    assert files.resolve_path(link) == target.resolve()
    assert files.resolve_path(link.parent / "other.robot") == (link.parent / "other.robot").resolve()


@pytest.mark.usefixtures("clear_resolved_paths")
def test_resolve_path_with_parent_reference(tmp_path):
    (tmp_path / "dir").mkdir()
    (tmp_path / "file.robot").touch()
    assert files.resolve_path(tmp_path / "dir" / ".." / "file.robot") == (tmp_path / "file.robot").resolve()


@pytest.mark.usefixtures("clear_resolved_paths")
def test_resolve_relative_path_after_changing_directory(tmp_path, monkeypatch):
    for project in ("first", "second"):
        (tmp_path / project / "dir").mkdir(parents=True)
        (tmp_path / project / "dir" / f"{project}.robot").touch()
    monkeypatch.chdir(tmp_path / "first")
    assert files.resolve_path(Path("dir", "first.robot")) == (tmp_path / "first" / "dir" / "first.robot").resolve()
    monkeypatch.chdir(tmp_path / "second")
    assert files.resolve_path(Path("dir", "second.robot")) == (tmp_path / "second" / "dir" / "second.robot").resolve()
