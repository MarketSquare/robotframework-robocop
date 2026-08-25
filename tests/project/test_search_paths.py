"""Tests for the ``--pythonpath`` search paths and the ``--variablefile`` option."""

from __future__ import annotations

import pytest

from robocop.config.manager import ConfigManager
from robocop.config.schema import RawConfig
from robocop.project.context import build_project_context
from robocop.project.definitions import ImportStatus, ImportType, Location, VariableDefinition
from robocop.project.imports import ImportResolver, build_search_paths
from robocop.project.variables import VariableScope, load_variable_files


@pytest.fixture
def project(tmp_path):
    (tmp_path / "libs").mkdir()
    (tmp_path / "libs" / "shared.resource").write_text("*** Keywords ***\nShared Keyword\n    Log    a\n")
    (tmp_path / "libs" / "MyLibrary.py").write_text("def keyword():\n    pass\n")
    (tmp_path / "libs" / "my_package").mkdir()
    (tmp_path / "libs" / "my_package" / "__init__.py").write_text("def keyword():\n    pass\n")
    (tmp_path / "test.robot").write_text(
        "*** Settings ***\nResource    shared.resource\n\n*** Test Cases ***\nTest\n    Shared Keyword\n"
    )
    return tmp_path


def location(source):
    return Location(source=source, lineno=1, col=1, end_lineno=1, end_col=1)


def resolve(project, name, import_type=ImportType.RESOURCE, search_paths=None):
    resolver = ImportResolver(VariableScope(project / "test.robot"), search_paths)
    return resolver.resolve(import_type, name, location(project / "test.robot"), project)


class TestBuildSearchPaths:
    def test_relative_to_root(self, project):
        assert build_search_paths(["libs"], project) == [(project / "libs").resolve()]

    def test_absolute_path(self, project):
        assert build_search_paths([str(project / "libs")], project) == [(project / "libs").resolve()]

    def test_glob_pattern(self, project):
        assert build_search_paths(["*"], project) == [(project / "libs").resolve()]

    def test_files_are_skipped(self, project):
        assert build_search_paths(["test.robot"], project) == []

    def test_missing_path_is_skipped(self, project):
        assert build_search_paths(["does_not_exist"], project) == []

    def test_duplicates_are_removed(self, project):
        assert build_search_paths(["libs", "libs", "./libs"], project) == [(project / "libs").resolve()]

    def test_order_is_kept(self, project):
        (project / "other").mkdir()
        assert build_search_paths(["other", "libs"], project) == [
            (project / "other").resolve(),
            (project / "libs").resolve(),
        ]


class TestResolveWithSearchPaths:
    def test_resource_not_found_without_search_path(self, project):
        assert resolve(project, "shared.resource").status == ImportStatus.NOT_FOUND

    def test_resource_found_in_search_path(self, project):
        result = resolve(project, "shared.resource", search_paths=[project / "libs"])
        assert result.status == ImportStatus.RESOLVED
        assert result.path == (project / "libs" / "shared.resource").resolve()

    def test_file_next_to_source_has_priority(self, project):
        (project / "shared.resource").write_text("*** Keywords ***\nLocal Keyword\n    Log    a\n")
        result = resolve(project, "shared.resource", search_paths=[project / "libs"])
        assert result.path == (project / "shared.resource").resolve()

    def test_library_file_found_in_search_path(self, project):
        result = resolve(project, "MyLibrary.py", ImportType.LIBRARY, search_paths=[project / "libs"])
        assert result.status == ImportStatus.RESOLVED

    def test_library_module_found_in_search_path(self, project):
        result = resolve(project, "MyLibrary", ImportType.LIBRARY, search_paths=[project / "libs"])
        assert result.status == ImportStatus.RESOLVED
        assert result.path == (project / "libs" / "MyLibrary.py").resolve()

    def test_library_package_found_in_search_path(self, project):
        result = resolve(project, "my_package", ImportType.LIBRARY, search_paths=[project / "libs"])
        assert result.path == (project / "libs" / "my_package" / "__init__.py").resolve()

    def test_library_module_not_in_search_path_is_external(self, project):
        result = resolve(project, "MyLibrary", ImportType.LIBRARY)
        assert result.status == ImportStatus.EXTERNAL

    def test_standard_library_is_never_searched(self, project):
        (project / "libs" / "Collections.py").write_text("def keyword():\n    pass\n")
        result = resolve(project, "Collections", ImportType.LIBRARY, search_paths=[project / "libs"])
        assert result.status == ImportStatus.EXTERNAL

    def test_variables_import_found_in_search_path(self, project):
        (project / "libs" / "vars.py").write_text("VALUE = 'value'\n")
        result = resolve(project, "vars.py", ImportType.VARIABLES, search_paths=[project / "libs"])
        assert result.status == ImportStatus.RESOLVED


class TestSearchPathsInProjectContext:
    def test_import_is_resolved_using_python_path(self, project):
        config_manager = ConfigManager(
            sources=[str(project)],
            root=project,
            ignore_file_config=True,
            overwrite_config=RawConfig(python_path=["libs"]),
        )
        context = build_project_context(config_manager, silent=True)
        imports = list(context.get_file(project / "test.robot").imports)
        assert [imported.status for imported in imports] == [ImportStatus.RESOLVED]

    def test_import_is_not_found_without_python_path(self, project):
        config_manager = ConfigManager(sources=[str(project)], root=project, ignore_file_config=True)
        context = build_project_context(config_manager, silent=True)
        imports = list(context.get_file(project / "test.robot").imports)
        assert [imported.status for imported in imports] == [ImportStatus.NOT_FOUND]


class TestVariableFiles:
    @pytest.fixture
    def variable_file(self, tmp_path):
        path = tmp_path / "vars.py"
        path.write_text("RESOURCE_DIR = 'resources'\nCOUNT = 5\n")
        return path

    def test_variables_are_loaded(self, variable_file):
        assert load_variable_files([str(variable_file)]) == {"RESOURCE_DIR": "resources"}

    def test_variable_file_found_in_search_path(self, variable_file):
        assert load_variable_files(["vars.py"], [variable_file.parent]) == {"RESOURCE_DIR": "resources"}

    def test_missing_variable_file_is_ignored(self):
        assert load_variable_files(["does_not_exist.py"]) == {}

    def test_broken_variable_file_is_ignored(self, tmp_path):
        path = tmp_path / "broken.py"
        path.write_text("raise RuntimeError('boom')\n")
        assert load_variable_files([str(path)]) == {}

    def test_variable_file_with_arguments(self, tmp_path):
        path = tmp_path / "args_vars.py"
        path.write_text("def get_variables(value):\n    return {'DIR': value}\n")
        assert load_variable_files([f"{path}:from_args"]) == {"DIR": "from_args"}

    def test_variables_are_used_to_resolve_imports(self, project):
        (project / "vars.py").write_text("RES_DIR = 'libs'\n")
        scope = VariableScope(project / "test.robot")
        scope.add_variable_files([str(project / "vars.py")])
        resolver = ImportResolver(scope)
        result = resolver.resolve(
            ImportType.RESOURCE, "${RES_DIR}/shared.resource", location(project / "test.robot"), project
        )
        assert result.status == ImportStatus.RESOLVED

    def test_command_line_variable_wins(self, project, variable_file):
        scope = VariableScope(project / "test.robot")
        scope.add_variable_files([str(variable_file)])
        scope.add_command_line({"RESOURCE_DIR": "from_cli"})
        assert scope.as_robot_variables().replace_string("${RESOURCE_DIR}") == "from_cli"

    def test_variable_file_wins_over_own_variables(self, project, variable_file):
        scope = VariableScope(project / "test.robot")
        scope.add_own([VariableDefinition(name="RESOURCE_DIR", normalized_name="resourcedir", value="own")])
        scope.add_variable_files([str(variable_file)])
        assert scope.as_robot_variables().replace_string("${RESOURCE_DIR}") == "resources"

    def test_copy_for_keeps_variable_files(self, project, variable_file):
        scope = VariableScope()
        scope.add_variable_files([str(variable_file)])
        copied = scope.copy_for(project / "test.robot")
        assert copied.as_robot_variables().replace_string("${RESOURCE_DIR}") == "resources"
