"""Tests for importing libraries to find out the keywords they provide."""

from __future__ import annotations

import os
import sys
import time

import pytest

from robocop.cache import RobocopCache
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

STDERR_LIBRARY = """
import sys

sys.stderr.write("noise\\n")


def stderr_keyword():
    pass
"""

LIBRARY_WITH_DUPLICATED_KEYWORDS = """
from robot.api.deco import keyword


@keyword("Defined twice")
def first():
    pass


@keyword("Defined twice")
def second():
    pass
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
        loader = LibraryLoader(timeout=2, workers=True)
        spec = loader.load(LibraryRequest(name="SlowLibrary", source=library_dir / "SlowLibrary.py"))
        assert not spec.loaded
        assert "timed out" in spec.error

    def test_libraries_are_imported_in_process_by_default(self, library_dir, monkeypatch):
        loader = build_library_loader(search_paths=[library_dir])
        monkeypatch.setattr(
            LibraryLoader,
            "_run_worker",
            lambda *args, **kwargs: pytest.fail("Library should be imported without a separate process"),  # noqa: ARG005
        )
        assert keyword_names(loader.load(LibraryRequest(name="MyLibrary"))) == ["Custom Keyword"]

    def test_workers_import_library_in_separate_process(self, library_dir, monkeypatch):
        loader = build_library_loader(search_paths=[library_dir], workers=True)
        monkeypatch.setattr(
            LibraryLoader,
            "_import_in_process",
            lambda *args, **kwargs: pytest.fail("Library should be imported in a separate process"),  # noqa: ARG005
        )
        assert keyword_names(loader.load(LibraryRequest(name="MyLibrary"))) == ["Custom Keyword"]

    def test_library_printing_on_import_does_not_write_to_output(self, library_dir, capsys):
        (library_dir / "NoisyLibrary.py").write_text("print('noise')\n\n\ndef noisy_keyword():\n    pass\n")
        loader = build_library_loader(search_paths=[library_dir])
        assert loader.load(LibraryRequest(name="NoisyLibrary")).loaded
        assert "noise" not in capsys.readouterr().out

    def test_library_writing_to_stderr_on_import_does_not_write_to_output(self, library_dir, capfd):
        (library_dir / "StderrLibrary.py").write_text(STDERR_LIBRARY)
        loader = build_library_loader(search_paths=[library_dir])
        assert loader.load(LibraryRequest(name="StderrLibrary")).loaded
        captured = capfd.readouterr()
        assert "noise" not in captured.err
        assert "noise" not in captured.out

    def test_robot_framework_errors_are_not_printed(self, library_dir, capfd):
        (library_dir / "DupeLibrary.py").write_text(LIBRARY_WITH_DUPLICATED_KEYWORDS)
        loader = build_library_loader(search_paths=[library_dir])
        assert loader.load(LibraryRequest(name="DupeLibrary")).loaded
        captured = capfd.readouterr()
        assert "Defined twice" not in captured.err
        assert "Defined twice" not in captured.out

    def test_output_streams_are_restored_after_import(self, library_dir):
        original_stdout, original_stderr = sys.__stdout__, sys.__stderr__
        loader = build_library_loader(search_paths=[library_dir])
        assert loader.load(LibraryRequest(name="MyLibrary")).loaded
        assert sys.__stdout__ is original_stdout
        assert sys.__stderr__ is original_stderr

    def test_scheduled_libraries_are_imported_in_parallel(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir], workers=True)
        requests = [LibraryRequest(name="MyLibrary"), LibraryRequest(name="ArgLibrary"), LibraryRequest(name="BuiltIn")]
        loader.schedule_preload(requests)
        assert keyword_names(loader.load(requests[0])) == ["Custom Keyword"]
        assert all(request.cache_key in loader._cache for request in requests)  # noqa: SLF001

    def test_scheduled_libraries_are_not_imported_without_workers(self, library_dir):
        loader = build_library_loader(search_paths=[library_dir])
        requests = [LibraryRequest(name="MyLibrary"), LibraryRequest(name="ArgLibrary")]
        loader.schedule_preload(requests)
        assert keyword_names(loader.load(requests[0])) == ["Custom Keyword"]
        assert requests[1].cache_key not in loader._cache  # noqa: SLF001

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

    def test_libraries_are_not_loaded_with_workers_by_default(self, project):
        context = build_context(project)
        assert not context.library_loader.workers

    def test_library_keywords_are_visible_with_workers(self, project):
        context = build_context(project, library_workers=True)
        assert context.library_loader.workers
        assert context.visible_keywords(project / "test.robot").find("Custom Keyword")
        assert context.visible_keywords(project / "test.robot").find("Append To List")
        assert context.visible_keywords(project / "test.robot").find("Log")


class TestPersistentLibraryCache:
    def test_library_is_read_from_cache_in_next_run(self, library_dir, tmp_path, monkeypatch):
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        loader = build_library_loader(search_paths=[library_dir], cache=cache)
        assert keyword_names(loader.load(LibraryRequest(name="MyLibrary"))) == ["Custom Keyword"]
        cache.save()

        next_cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        next_loader = build_library_loader(search_paths=[library_dir], cache=next_cache)
        for method in ("_run_worker", "_import_in_process"):
            monkeypatch.setattr(
                LibraryLoader,
                method,
                lambda *args, **kwargs: pytest.fail("Library should be read from the cache"),  # noqa: ARG005
            )
        assert keyword_names(next_loader.load(LibraryRequest(name="MyLibrary"))) == ["Custom Keyword"]

    def test_modified_library_is_imported_again(self, library_dir, tmp_path):
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        loader = build_library_loader(search_paths=[library_dir], cache=cache)
        loader.load(LibraryRequest(name="MyLibrary"))
        cache.save()

        library = library_dir / "MyLibrary.py"
        library.write_text("def other_keyword():\n    pass\n")
        os.utime(library, (time.time() + 10, time.time() + 10))

        next_cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        next_loader = build_library_loader(search_paths=[library_dir], cache=next_cache)
        assert keyword_names(next_loader.load(LibraryRequest(name="MyLibrary"))) == ["Other Keyword"]

    def test_failed_import_is_not_cached(self, library_dir, tmp_path):
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        loader = build_library_loader(search_paths=[library_dir], cache=cache)
        assert not loader.load(LibraryRequest(name="BrokenLibrary")).loaded
        assert not cache.data.libraries

    def test_project_libraries_are_not_cached(self, library_dir, tmp_path):
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        loader = build_library_loader(search_paths=[library_dir], cache=cache, project_root=library_dir)
        assert loader.load(LibraryRequest(name="MyLibrary")).loaded
        assert not cache.data.libraries

    def test_cache_is_not_used_when_environment_changes(self, library_dir, tmp_path):
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        loader = build_library_loader(search_paths=[library_dir], cache=cache)
        loader.load(LibraryRequest(name="MyLibrary"))
        key = next(iter(cache.data.libraries))
        assert cache.get_library_entry(key, "other-environment") is None
