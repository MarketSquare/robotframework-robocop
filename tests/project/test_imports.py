from pathlib import Path

import pytest

from robocop.project.definitions import ImportStatus, ImportType, Location, VariableDefinition
from robocop.project.imports import ImportResolver
from robocop.project.variables import VariableScope


@pytest.fixture
def project(tmp_path):
    (tmp_path / "resources").mkdir()
    (tmp_path / "resources" / "common.resource").write_text("*** Keywords ***\nKeyword\n    Log    a\n")
    (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Keyword\n")
    return tmp_path


def location(source: Path) -> Location:
    return Location(source=source, lineno=1, col=1, end_lineno=1, end_col=1)


def resolve(scope: VariableScope, name: str, base_dir: Path, import_type: ImportType = ImportType.RESOURCE):
    resolver = ImportResolver(scope)
    return resolver.resolve(import_type, name, location(base_dir / "test.robot"), base_dir)


class TestImportResolver:
    def test_existing_relative_path(self, project):
        result = resolve(VariableScope(project / "test.robot"), "resources/common.resource", project)
        assert result.status == ImportStatus.RESOLVED
        assert result.path == (project / "resources" / "common.resource").resolve()

    def test_missing_path(self, project):
        result = resolve(VariableScope(project / "test.robot"), "resources/missing.resource", project)
        assert result.status == ImportStatus.NOT_FOUND
        assert result.path is None

    def test_variable_in_path_is_resolved(self, project):
        scope = VariableScope(project / "test.robot")
        scope.add_command_line({"RES_DIR": "resources"})
        result = resolve(scope, "${RES_DIR}/common.resource", project)
        assert result.status == ImportStatus.RESOLVED
        assert result.resolved_name == "resources/common.resource"

    def test_unresolvable_variable_is_not_reported(self, project):
        result = resolve(VariableScope(project / "test.robot"), "${UNKNOWN}/common.resource", project)
        assert result.status == ImportStatus.UNRESOLVABLE
        assert result.path is None

    def test_curdir_is_resolved_against_source(self, project):
        scope = VariableScope(project / "test.robot")
        result = resolve(scope, "${CURDIR}/resources/common.resource", project)
        assert result.status == ImportStatus.RESOLVED

    def test_environment_variable(self, project, monkeypatch):
        monkeypatch.setenv("ROBOCOP_TEST_DIR", "resources")
        result = resolve(VariableScope(project / "test.robot"), "%{ROBOCOP_TEST_DIR}/common.resource", project)
        assert result.status == ImportStatus.RESOLVED

    def test_environment_variable_default(self, project):
        result = resolve(VariableScope(project / "test.robot"), "%{NOT_SET=resources}/common.resource", project)
        assert result.status == ImportStatus.RESOLVED

    def test_standard_library_is_external(self, project):
        result = resolve(VariableScope(project / "test.robot"), "Collections", project, ImportType.LIBRARY)
        assert result.status == ImportStatus.EXTERNAL

    def test_module_library_is_external(self, project):
        result = resolve(VariableScope(project / "test.robot"), "my_package.MyLibrary", project, ImportType.LIBRARY)
        assert result.status == ImportStatus.EXTERNAL

    def test_library_file_is_resolved(self, project):
        (project / "MyLib.py").write_text("def keyword():\n    pass\n")
        result = resolve(VariableScope(project / "test.robot"), "MyLib.py", project, ImportType.LIBRARY)
        assert result.status == ImportStatus.RESOLVED


class TestVariableScope:
    def test_command_line_overrides_own(self, tmp_path):
        scope = VariableScope(tmp_path / "test.robot")
        scope.add_own([VariableDefinition(name="DIR", normalized_name="dir", value="own")])
        scope.add_command_line({"DIR": "cli"})
        assert scope.as_robot_variables().replace_string("${DIR}") == "cli"

    def test_own_overrides_imported(self, tmp_path):
        scope = VariableScope(tmp_path / "test.robot")
        scope.add_imported([VariableDefinition(name="DIR", normalized_name="dir", value="imported")])
        scope.add_own([VariableDefinition(name="DIR", normalized_name="dir", value="own")])
        assert scope.as_robot_variables().replace_string("${DIR}") == "own"

    def test_copy_for_keeps_command_line_only(self, tmp_path):
        scope = VariableScope()
        scope.add_command_line({"DIR": "cli"})
        scope.add_own([VariableDefinition(name="OWN", normalized_name="own", value="value")])
        copied = scope.copy_for(tmp_path / "other.robot")
        assert copied.as_robot_variables().replace_string("${DIR}") == "cli"
        assert copied.source == tmp_path / "other.robot"
