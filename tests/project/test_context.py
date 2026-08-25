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


class TestKeywordVisibility:
    def test_own_and_imported_keywords_are_visible(self, context, project):
        visible = context.visible_keywords(project / "test.robot")
        assert visible.find("Common Keyword")
        assert visible.find("Login As bob")

    def test_private_keyword_of_imported_file_is_not_visible(self, context, project):
        visible = context.visible_keywords(project / "test.robot")
        assert not visible.find("Private Keyword")

    def test_private_keyword_is_visible_in_own_file(self, context, project):
        visible = context.visible_keywords(project / "resources" / "common.resource")
        assert visible.find("Private Keyword")

    def test_imported_files_include_itself(self, context, project):
        paths = {file.path for file in context.imported_files(project / "test.robot")}
        assert paths == {project / "test.robot", project / "resources" / "common.resource"}

    def test_unknown_file_has_no_imports(self, context, project):
        assert context.imported_files(project / "does_not_exist.robot") == []

    def test_resolve_keyword_uses_imports(self, context, project):
        usages = context.get_file(project / "test.robot").usages
        by_name = {usage.name: usage for usage in usages}
        assert len(context.resolve_keyword(by_name["Common Keyword"])) == 1
        assert len(context.resolve_keyword(by_name["Login As bob"])) == 1


class TestUsageArguments:
    def test_arguments_are_collected(self, context, project):
        usages = context.get_file(project / "test.robot").usages
        by_name = {usage.name: usage for usage in usages}
        assert by_name["Common Keyword"].arguments == ("1",)
        assert by_name["Common Keyword"].argument_count == 1
        assert by_name["Login As bob"].arguments == ()


class TestUsedVariables:
    def test_defined_but_never_used_variable(self, context, project):
        project_file = context.get_file(project / "test.robot")
        assert "greeting" not in project_file.used_variables

    def test_variables_used_in_resource(self, context, project):
        resource = context.get_file(project / "resources" / "common.resource")
        assert {"a", "user"} <= resource.used_variables

    def test_variable_definition_is_not_usage(self, tmp_path):
        (tmp_path / "vars.robot").write_text("*** Variables ***\n${ONLY_DEFINED}    value\n")
        config_manager = ConfigManager(sources=[str(tmp_path)], root=tmp_path, ignore_file_config=True)
        context = build_project_context(config_manager, silent=True)
        project_file = context.get_file(tmp_path / "vars.robot")
        assert "onlydefined" not in project_file.used_variables

    def test_variable_used_as_value_of_other_variable(self, tmp_path):
        (tmp_path / "vars.robot").write_text("*** Variables ***\n${A}    value\n${B}    ${A}-suffix\n")
        config_manager = ConfigManager(sources=[str(tmp_path)], root=tmp_path, ignore_file_config=True)
        context = build_project_context(config_manager, silent=True)
        project_file = context.get_file(tmp_path / "vars.robot")
        assert "a" in project_file.used_variables

    def test_nested_variables_are_collected(self, tmp_path):
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    ${outer.${inner}}\n")
        config_manager = ConfigManager(sources=[str(tmp_path)], root=tmp_path, ignore_file_config=True)
        context = build_project_context(config_manager, silent=True)
        used = context.get_file(tmp_path / "test.robot").used_variables
        assert "inner" in used


class TestDynamicKeywordCalls:
    def test_no_dynamic_calls(self, context, project):
        assert not context.get_file(project / "test.robot").has_dynamic_keyword_calls

    def test_dynamic_call_detected(self, tmp_path):
        (tmp_path / "test.robot").write_text(
            "*** Variables ***\n${KW}    Log\n\n*** Test Cases ***\nTest\n    Run Keyword    ${KW}\n"
        )
        config_manager = ConfigManager(sources=[str(tmp_path)], root=tmp_path, ignore_file_config=True)
        context = build_project_context(config_manager, silent=True)
        assert context.get_file(tmp_path / "test.robot").has_dynamic_keyword_calls


@pytest.fixture
def circular_project(tmp_path):
    """Project where resources import each other, including a file importing itself."""
    (tmp_path / "a.resource").write_text(
        "*** Settings ***\nResource    b.resource\n\n*** Keywords ***\nKeyword A\n    Keyword B\n"
    )
    (tmp_path / "b.resource").write_text(
        "*** Settings ***\nResource    a.resource\n\n*** Keywords ***\nKeyword B\n    Keyword A\n"
    )
    (tmp_path / "self.resource").write_text(
        "*** Settings ***\nResource    self.resource\n\n*** Keywords ***\nSelf Keyword\n    Log    a\n"
    )
    (tmp_path / "test.robot").write_text(
        "*** Settings ***\n"
        "Resource    a.resource\n"
        "Resource    self.resource\n"
        "\n"
        "*** Test Cases ***\n"
        "Test\n"
        "    Keyword A\n"
        "    Self Keyword\n"
    )
    return tmp_path


@pytest.fixture
def circular_context(circular_project):
    config_manager = ConfigManager(sources=[str(circular_project)], root=circular_project, ignore_file_config=True)
    return build_project_context(config_manager, silent=True)


class TestCircularImports:
    """Circular imports are allowed in Robot Framework, so they must not break the analysis."""

    def test_every_file_is_visited_once(self, circular_context, circular_project):
        visible = circular_context.imported_files(circular_project / "a.resource")
        assert [file.path.name for file in visible] == ["a.resource", "b.resource"]

    def test_file_importing_itself(self, circular_context, circular_project):
        visible = circular_context.imported_files(circular_project / "self.resource")
        assert [file.path.name for file in visible] == ["self.resource"]

    def test_keywords_from_cycle_are_visible(self, circular_context, circular_project):
        index = circular_context.visible_keywords(circular_project / "test.robot")
        assert index.find("Keyword A")
        assert index.find("Keyword B")
        assert index.find("Self Keyword")

    def test_usages_are_resolved(self, circular_context):
        usages = [usage for _, usage in circular_context.iter_usages() if usage.name == "Keyword A"]
        assert all(circular_context.resolve_keyword(usage) for usage in usages)
