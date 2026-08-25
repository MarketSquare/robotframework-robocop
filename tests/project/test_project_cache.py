import os
import time

import pytest

from robocop.config.manager import ConfigManager
from robocop.config.parser import load_languages
from robocop.config.schema import RawCacheConfig, RawConfig
from robocop.project.collector import ProjectFileCollector
from robocop.project.context import build_project_context, collection_hash
from robocop.project.serialization import collected_file_from_dict, collected_file_to_dict
from robocop.version_handling import ROBOT_VERSION, Version

pytestmark_languages = pytest.mark.skipif(
    ROBOT_VERSION < Version("6.0"),  # noqa: SIM300
    reason="Languages are supported since RF 6.0",
)


@pytest.fixture
def project(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "common.resource").write_text(
        "*** Keywords ***\n"
        "Common Keyword\n"
        "    [Arguments]    ${a}    ${b}=2\n"
        "    Log    ${a}\n"
        "\n"
        "Login As ${user}\n"
        "    Log    ${user}\n"
        "\n"
        "Private Keyword\n"
        "    [Tags]    robot:private\n"
        "    Log    private\n"
    )
    (source / "test.robot").write_text(
        "*** Settings ***\n"
        "Resource    common.resource\n"
        "Library     Collections    AS    Col\n"
        "\n"
        "*** Variables ***\n"
        "${GREETING}     hello\n"
        "\n"
        "*** Test Cases ***\n"
        "Test\n"
        "    [Setup]    Common Keyword    1\n"
        "    Login As bob\n"
        "    Log    ${GREETING}\n"
    )
    return source


def build_context(project, cache_dir, enabled=True, **config):
    config_manager = ConfigManager(
        sources=[str(project)],
        root=project,
        ignore_file_config=True,
        overwrite_config=RawConfig(cache=RawCacheConfig(enabled=enabled, cache_dir=cache_dir), **config),
    )
    context = build_project_context(config_manager, silent=True)
    config_manager.cache.save()
    return context


def count_collected(project, cache_dir, **config):
    """
    Build the context and count how many files had to be collected instead of being read from the cache.

    Returns:
        Number of files parsed and collected during the run.

    """
    collected = 0
    original = ProjectFileCollector.collect

    def counting_collect(self, model):
        nonlocal collected
        collected += 1
        return original(self, model)

    with pytest.MonkeyPatch.context() as monkeypatch:
        monkeypatch.setattr(ProjectFileCollector, "collect", counting_collect)
        build_context(project, cache_dir, **config)
    return collected


def describe(context):
    """Describe the collected data in a way that can be compared between the runs."""
    described = {}
    for path, project_file in sorted(context.files.items()):
        described[path.name] = {
            "is_suite": project_file.is_suite,
            "keywords": [
                (
                    keyword.name,
                    keyword.location.lineno,
                    keyword.location.col,
                    keyword.is_private,
                    keyword.has_embedded_arguments,
                    keyword.arguments.describe_accepted(),
                )
                for keyword in project_file.keywords
            ],
            "usages": [
                (usage.name, usage.location.lineno, usage.arguments, usage.is_template) for usage in project_file.usages
            ],
            "variables": [(variable.name, variable.value) for variable in project_file.variables],
            "used_variables": sorted(project_file.used_variables),
            "imports": [
                (imported.import_type.value, imported.resolved_name, imported.status.value, imported.alias)
                for imported in project_file.imports
            ],
        }
    return described


class TestProjectCache:
    def test_collected_data_is_stored_in_cache(self, project, tmp_path):
        assert count_collected(project, tmp_path / "cache") == 2
        assert count_collected(project, tmp_path / "cache") == 0

    def test_files_are_not_parsed_again_in_next_run(self, project, tmp_path, monkeypatch):
        expected = describe(build_context(project, tmp_path / "cache"))

        monkeypatch.setattr(
            ProjectFileCollector,
            "collect",
            lambda *args, **kwargs: pytest.fail("File should be read from the cache"),  # noqa: ARG005
        )
        assert describe(build_context(project, tmp_path / "cache")) == expected

    def test_modified_file_is_collected_again(self, project, tmp_path):
        build_context(project, tmp_path / "cache")

        test_file = project / "test.robot"
        test_file.write_text("*** Keywords ***\nOther Keyword\n    Log    a\n")
        os.utime(test_file, (time.time() + 10, time.time() + 10))

        context = build_context(project, tmp_path / "cache")
        assert [keyword.name for keyword in context.get_file(test_file).keywords] == ["Other Keyword"]

    @pytestmark_languages
    def test_cache_is_not_used_when_language_changes(self, project, tmp_path):
        build_context(project, tmp_path / "cache")
        collected = count_collected(project, tmp_path / "cache", language=["pl"])
        assert collected == 2

    def test_nothing_is_stored_when_cache_is_disabled(self, project, tmp_path):
        config_manager = ConfigManager(
            sources=[str(project)],
            root=project,
            ignore_file_config=True,
            overwrite_config=RawConfig(cache=RawCacheConfig(enabled=False, cache_dir=tmp_path / "cache")),
        )
        build_project_context(config_manager, silent=True)
        assert not config_manager.cache.data.project

    def test_embedded_keyword_still_matches_after_restoring(self, project, tmp_path):
        build_context(project, tmp_path / "cache")
        context = build_context(project, tmp_path / "cache")
        assert context.visible_keywords(project / "test.robot").find("login as ANNE")


class TestCollectionHash:
    def test_same_configuration_gives_same_hash(self):
        assert collection_hash(None) == collection_hash(None)

    @pytestmark_languages
    def test_language_changes_the_hash(self):
        assert collection_hash(None) != collection_hash(load_languages(["pl"]))


class TestSerialization:
    def test_round_trip_keeps_collected_data(self, project, tmp_path):
        context = build_context(project, tmp_path / "cache", enabled=False)
        for path, project_file in context.files.items():
            restored = collected_file_from_dict(collected_file_to_dict(project_file.collected), path)
            assert restored == project_file.collected

    def test_unknown_format_is_ignored(self, tmp_path):
        assert collected_file_from_dict({"version": -1}, tmp_path) is None
