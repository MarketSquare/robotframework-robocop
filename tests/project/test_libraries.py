"""Tests for importing libraries to find out the keywords they provide."""

from __future__ import annotations

import pytest

from robocop.config.manager import ConfigManager
from robocop.config.schema import RawConfig
from robocop.project.context import build_project_context
from robocop.project.libraries import LibraryLoader, LibraryRequest, build_library_loader

SLOW_LIBRARY = """
import time

time.sleep(30)


def slow_keyword():
    pass
"""

BROKEN_LIBRARY = """
raise RuntimeError("boom")
"""

LIBRARY_WITH_ARGUMENTS = """
class ArgLibrary:
    def __init__(self, mode="basic"):
        self.mode = mode

    def basic_keyword(self, first):
        pass

    def extra_keyword(self, first, second):
        pass
"""


@pytest.fixture
def library_dir(tmp_path):
    (tmp_path / "MyLibrary.py").write_text("def custom_keyword(first, second='default'):\n    pass\n")
    (tmp_path / "SlowLibrary.py").write_text(SLOW_LIBRARY)
    (tmp_path / "BrokenLibrary.py").write_text(BROKEN_LIBRARY)
    (tmp_path / "ArgLibrary.py").write_text(LIBRARY_WITH_ARGUMENTS)
    return tmp_path


def keyword_names(spec):
    return sorted(keyword.name for keyword in spec.keywords)


class TestLibraryLoader:
    def test_standard_library_is_imported(self):
        spec = LibraryLoader().load(LibraryRequest(name="Collections"))
        assert spec.loaded
        assert "Append To List" in keyword_names(spec)

    def test_keyword_arguments_are_read(self):
        spec = LibraryLoader().load(LibraryRequest(name="Collections"))
        keyword = next(keyword for keyword in spec.keywords if keyword.name == "Append To List")
        assert keyword.arguments.positional == ("list_",)
        assert keyword.arguments.var_positional == "values"
        assert keyword.library_name == "Collections"

    def test_library_from_search_path(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir])
        spec = loader.load(LibraryRequest(name="MyLibrary"))
        assert keyword_names(spec) == ["Custom Keyword"]

    def test_library_from_path(self, library_dir):
        spec = LibraryLoader().load(LibraryRequest(name="MyLibrary", source=library_dir / "MyLibrary.py"))
        assert keyword_names(spec) == ["Custom Keyword"]

    def test_missing_library(self):
        spec = LibraryLoader().load(LibraryRequest(name="ThereIsNoSuchLibrary"))
        assert not spec.loaded
        assert spec.keywords == ()
        assert "ThereIsNoSuchLibrary" in spec.error

    def test_library_raising_on_import(self, library_dir):
        spec = LibraryLoader().load(LibraryRequest(name="BrokenLibrary", source=library_dir / "BrokenLibrary.py"))
        assert not spec.loaded
        assert spec.keywords == ()

    def test_import_timeout(self, library_dir):
        loader = LibraryLoader(timeout=2)
        spec = loader.load(LibraryRequest(name="SlowLibrary", source=library_dir / "SlowLibrary.py"))
        assert not spec.loaded
        assert "timed out" in spec.error

    def test_ignored_library(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir], ignored_libraries=["My*"])
        spec = loader.load(LibraryRequest(name="MyLibrary"))
        assert not spec.loaded
        assert spec.keywords == ()

    def test_library_arguments_change_keywords(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir])
        spec = loader.load(LibraryRequest(name="ArgLibrary", args=("extra",)))
        assert "Extra Keyword" in keyword_names(spec)

    def test_alias_is_used_as_library_name(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir])
        spec = loader.load(LibraryRequest(name="MyLibrary", alias="Renamed"))
        assert spec.name == "Renamed"
        assert all(keyword.library_name == "Renamed" for keyword in spec.keywords)

    def test_library_is_imported_only_once(self, library_dir, monkeypatch):
        loader = build_library_loader(search_paths=[library_dir])
        loader.load(LibraryRequest(name="MyLibrary"))
        monkeypatch.setattr(
            LibraryLoader,
            "_load",
            lambda *args, **kwargs: pytest.fail("Library should be imported only once"),  # noqa: ARG005
        )
        assert keyword_names(loader.load(LibraryRequest(name="MyLibrary"))) == ["Custom Keyword"]


@pytest.fixture
def project(tmp_path):
    (tmp_path / "MyLibrary.py").write_text("def custom_keyword(first, second='default'):\n    pass\n")
    (tmp_path / "test.robot").write_text(
        "*** Settings ***\n"
        "Library    MyLibrary.py\n"
        "Library    Collections\n"
        "\n"
        "*** Test Cases ***\n"
        "Test\n"
        "    Custom Keyword    1\n"
    )
    return tmp_path


def build_context(project, **config):
    config_manager = ConfigManager(
        sources=[str(project)],
        root=project,
        ignore_file_config=True,
        overwrite_config=RawConfig(**config),
    )
    return build_project_context(config_manager, silent=True)


class TestLibrariesInProjectContext:
    def test_library_keywords_are_visible(self, project):
        context = build_context(project)
        assert context.visible_keywords(project / "test.robot").find("Custom Keyword")
        assert context.visible_keywords(project / "test.robot").find("Append To List")

    def test_builtin_keywords_are_visible(self, project):
        context = build_context(project)
        assert context.visible_keywords(project / "test.robot").find("Log")

    def test_libraries_are_not_imported_when_disabled(self, project):
        context = build_context(project, analyze_libraries=False)
        assert context.library_loader is None
        assert not context.visible_keywords(project / "test.robot").find("Custom Keyword")

    def test_ignored_library_is_not_imported(self, project):
        context = build_context(project, ignored_libraries=["MyLibrary*"])
        assert not context.visible_keywords(project / "test.robot").find("Custom Keyword")
        assert context.visible_keywords(project / "test.robot").find("Append To List")

    def test_project_keywords_are_still_visible(self, project):
        (project / "test.robot").write_text(
            "*** Test Cases ***\nTest\n    Own Keyword\n\n*** Keywords ***\nOwn Keyword\n    Log    a\n"
        )
        context = build_context(project)
        assert context.visible_keywords(project / "test.robot").find("Own Keyword")
