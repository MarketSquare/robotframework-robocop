import pytest

from robocop.config.manager import ConfigManager
from robocop.project.context import build_project_context


@pytest.fixture
def project(tmp_path):
    (tmp_path / "resources").mkdir()
    (tmp_path / "resources" / "common.resource").write_text(
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
    (tmp_path / "test.robot").write_text(
        "*** Settings ***\n"
        "Resource    resources/common.resource\n"
        "Resource    resources/missing.resource\n"
        "Library     Collections\n"
        "\n"
        "*** Variables ***\n"
        "${GREETING}     hello\n"
        "\n"
        "*** Test Cases ***\n"
        "Test\n"
        "    Common Keyword    1\n"
        "    Login As bob\n"
    )
    return tmp_path


@pytest.fixture
def context(project):
    config_manager = ConfigManager(sources=[str(project)], root=project, ignore_file_config=True)
    return build_project_context(config_manager, silent=True)


class TestProjectContext:
    def test_all_files_are_collected(self, context, project):
        assert set(context.files) == {
            (project / "test.robot").resolve(),
            (project / "resources" / "common.resource").resolve(),
        }

    def test_suite_and_resource_are_recognized(self, context, project):
        assert context.get_file(project / "test.robot").is_suite
        assert context.get_file(project / "resources" / "common.resource").is_resource

    def test_keyword_definitions_are_indexed(self, context):
        assert [keyword.name for keyword in context.keywords.find("Common Keyword")] == ["Common Keyword"]

    def test_keyword_arguments_are_parsed(self, context):
        keyword = context.keywords.find("Common Keyword")[0]
        assert keyword.arguments.min_args == 1
        assert keyword.arguments.max_args == 2

    def test_embedded_keyword_is_matched(self, context):
        assert [keyword.name for keyword in context.keywords.find("Login As bob")] == ["Login As ${user}"]

    def test_private_keyword_is_marked(self, context):
        keyword = context.keywords.find("Private Keyword")[0]
        assert keyword.is_private

    def test_unknown_keyword_is_not_found(self, context):
        assert context.keywords.find("No Such Keyword") == []

    def test_keyword_usages_are_collected(self, context, project):
        usages = {usage.name for usage in context.get_file(project / "test.robot").usages}
        assert usages == {"Common Keyword", "Login As bob"}

    def test_usage_argument_count(self, context, project):
        usage = next(u for u in context.get_file(project / "test.robot").usages if u.name == "Common Keyword")
        assert usage.argument_count == 1

    def test_variables_are_collected(self, context, project):
        variables = {variable.name for variable in context.get_file(project / "test.robot").variables}
        assert variables == {"GREETING"}

    def test_imports_are_resolved(self, context, project):
        imports = context.get_file(project / "test.robot").imports
        statuses = {imported.name: imported.status.value for imported in imports}
        assert statuses == {
            "resources/common.resource": "resolved",
            "resources/missing.resource": "not_found",
            "Collections": "external",
        }
