"""Tests for MCP prompts."""

import asyncio

import pytest

from robocop.mcp import mcp


@pytest.fixture(scope="module")
def mcp_prompts():
    """Get the registered MCP prompts."""

    async def get_prompts():
        return await mcp.get_prompts()

    return asyncio.run(get_prompts())


def get_prompt_result(prompt, **kwargs):
    """Call prompt function and return the result."""
    # Prompt functions return strings directly (not coroutines)
    return prompt.fn(**kwargs)


class TestAnalyzeRobotFilePrompt:
    """Tests for analyze_robot_file prompt."""

    def test_prompt_with_all_focus(self, mcp_prompts):
        """Test prompt generation with focus='all'."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello")

        assert "lint_content" in result
        assert "all types of issues" in result
        assert "*** Test Cases ***" in result

    def test_prompt_with_style_focus(self, mcp_prompts):
        """Test prompt generation with focus='style'."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello", focus="style")

        assert "style" in result.lower()
        assert "naming conventions" in result.lower()

    def test_prompt_with_errors_focus(self, mcp_prompts):
        """Test prompt generation with focus='errors'."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello", focus="errors")

        assert "critical errors" in result.lower()
        assert "test failures" in result.lower()

    def test_prompt_with_best_practices_focus(self, mcp_prompts):
        """Test prompt generation with focus='best-practices'."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello", focus="best-practices")

        assert "best practices" in result.lower()
        assert "maintainability" in result.lower()

    def test_prompt_with_invalid_focus_uses_default(self, mcp_prompts):
        """Test that invalid focus falls back to 'all'."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello", focus="invalid")

        # Should fall back to "all" focus
        assert "all types of issues" in result

    def test_prompt_includes_instructions(self, mcp_prompts):
        """Test that prompt includes proper instructions."""
        prompt = mcp_prompts["analyze_robot_file"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello")

        assert "Instructions" in result
        assert "Summarize" in result
        assert "severity" in result


class TestFixRobotIssuesPrompt:
    """Tests for fix_robot_issues prompt."""

    def test_prompt_structure(self, mcp_prompts):
        """Test that prompt has expected structure."""
        prompt = mcp_prompts["fix_robot_issues"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\ntest\n    log  hello")

        assert "Fix all issues" in result
        assert "lint_content" in result
        assert "format_content" in result
        assert "*** Test Cases ***" in result

    def test_prompt_includes_preservation_notes(self, mcp_prompts):
        """Test that prompt mentions preserving test logic."""
        prompt = mcp_prompts["fix_robot_issues"]
        result = get_prompt_result(prompt, content="*** Test Cases ***\nTest\n    Log    Hello")

        assert "Preserve" in result
        assert "original test logic" in result.lower()

    def test_prompt_includes_code_to_fix(self, mcp_prompts):
        """Test that prompt includes the provided code."""
        prompt = mcp_prompts["fix_robot_issues"]
        test_content = "*** Keywords ***\nMy Special Keyword\n    Log    Special\n"
        result = get_prompt_result(prompt, content=test_content)

        assert "My Special Keyword" in result
        assert "Code to fix" in result


class TestExplainRulePrompt:
    """Tests for explain_rule prompt."""

    def test_prompt_without_code_snippet(self, mcp_prompts):
        """Test prompt when no code snippet is provided."""
        prompt = mcp_prompts["explain_rule"]
        result = get_prompt_result(prompt, rule_name_or_id="LEN01")

        assert "LEN01" in result
        assert "get_rule_info" in result
        assert "Code that triggered" not in result

    def test_prompt_with_code_snippet(self, mcp_prompts):
        """Test prompt when code snippet is provided."""
        prompt = mcp_prompts["explain_rule"]
        code = "*** Test Cases ***\nVery Long Test Case Name That Exceeds Limits\n    Log    Hi"
        result = get_prompt_result(prompt, rule_name_or_id="LEN01", code_snippet=code)

        assert "LEN01" in result
        assert "Code that triggered" in result
        assert "Very Long Test Case Name" in result
        assert "how to fix" in result.lower()

    def test_prompt_includes_configuration_guidance(self, mcp_prompts):
        """Test that prompt mentions configurable parameters."""
        prompt = mcp_prompts["explain_rule"]
        result = get_prompt_result(prompt, rule_name_or_id="line-too-long")

        assert "configurable parameters" in result.lower()

    def test_prompt_with_rule_name(self, mcp_prompts):
        """Test prompt with rule name instead of ID."""
        prompt = mcp_prompts["explain_rule"]
        result = get_prompt_result(prompt, rule_name_or_id="not-capitalized-test-case-title")

        assert "not-capitalized-test-case-title" in result


class TestReviewPullRequestPrompt:
    """Tests for review_pull_request prompt."""

    def test_prompt_with_single_file(self, mcp_prompts):
        """Test prompt with a single file path."""
        prompt = mcp_prompts["review_pull_request"]
        result = get_prompt_result(prompt, file_paths="tests/test_login.robot")

        assert "test_login.robot" in result
        assert "lint_file" in result
        assert "pull request" in result.lower()

    def test_prompt_with_multiple_files(self, mcp_prompts):
        """Test prompt with comma-separated file paths."""
        prompt = mcp_prompts["review_pull_request"]
        result = get_prompt_result(prompt, file_paths="test1.robot, test2.robot, lib.resource")

        assert "test1.robot" in result
        assert "test2.robot" in result
        assert "lib.resource" in result

    def test_prompt_includes_review_checklist(self, mcp_prompts):
        """Test that prompt includes review checklist items."""
        prompt = mcp_prompts["review_pull_request"]
        result = get_prompt_result(prompt, file_paths="test.robot")

        assert "naming conventions" in result.lower()
        assert "documentation" in result.lower()
        assert "Must-fix" in result

    def test_prompt_output_format(self, mcp_prompts):
        """Test that prompt specifies output format."""
        prompt = mcp_prompts["review_pull_request"]
        result = get_prompt_result(prompt, file_paths="test.robot")

        assert "Output format" in result
        assert "pull request comment" in result.lower()


class TestConfigureRobocopPrompt:
    """Tests for configure_robocop prompt."""

    def test_prompt_generic_project(self, mcp_prompts):
        """Test prompt for generic project type."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="generic")

        assert "general-purpose" in result
        assert "list_rules" in result
        assert "list_formatters" in result

    def test_prompt_api_testing_project(self, mcp_prompts):
        """Test prompt for API testing project type."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="api-testing")

        assert "API testing" in result
        assert "RequestsLibrary" in result or "REST" in result

    def test_prompt_ui_testing_project(self, mcp_prompts):
        """Test prompt for UI testing project type."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="ui-testing")

        assert "UI" in result or "browser" in result.lower()

    def test_prompt_data_driven_project(self, mcp_prompts):
        """Test prompt for data-driven project type."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="data-driven")

        assert "data-driven" in result
        assert "templates" in result.lower() or "variables" in result.lower()

    def test_prompt_unknown_type_uses_generic(self, mcp_prompts):
        """Test that unknown project type falls back to generic."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="unknown-type")

        assert "general-purpose" in result

    def test_prompt_includes_ci_cd_suggestions(self, mcp_prompts):
        """Test that prompt includes CI/CD integration suggestions."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="generic")

        assert "CI/CD" in result
        assert "pre-commit" in result.lower() or "GitHub Actions" in result

    def test_prompt_includes_config_file_sample(self, mcp_prompts):
        """Test that prompt mentions .robocop configuration file."""
        prompt = mcp_prompts["configure_robocop"]
        result = get_prompt_result(prompt, project_type="generic")

        assert ".robocop" in result


class TestMigrateToLatestPrompt:
    """Tests for migrate_to_latest prompt."""

    def test_prompt_default_version(self, mcp_prompts):
        """Test prompt with default version (4.x)."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt)

        assert "4.x" in result
        assert "7.x" in result
        assert "deprecated" in result.lower()

    def test_prompt_custom_version(self, mcp_prompts):
        """Test prompt with custom version."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt, current_rf_version="5.x")

        assert "5.x" in result
        assert "7.x" in result

    def test_prompt_includes_migration_steps(self, mcp_prompts):
        """Test that prompt includes migration steps."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt, current_rf_version="4.x")

        assert "deprecated patterns" in result.lower()
        assert "replacement" in result.lower()
        assert "before/after" in result.lower() or "code examples" in result.lower()

    def test_prompt_includes_priority_order(self, mcp_prompts):
        """Test that prompt mentions priority order for fixes."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt)

        assert "Priority" in result or "breaking changes" in result.lower()

    def test_prompt_includes_testing_recommendations(self, mcp_prompts):
        """Test that prompt includes testing recommendations."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt)

        assert "Testing" in result or "testing" in result

    def test_prompt_mentions_list_rules(self, mcp_prompts):
        """Test that prompt mentions using list_rules."""
        prompt = mcp_prompts["migrate_to_latest"]
        result = get_prompt_result(prompt)

        assert "list_rules" in result


class TestPromptRegistration:
    """Tests for prompt registration."""

    def test_all_prompts_registered(self, mcp_prompts):
        """Test that all 6 prompts are registered."""
        expected_prompts = [
            "analyze_robot_file",
            "fix_robot_issues",
            "explain_rule",
            "review_pull_request",
            "configure_robocop",
            "migrate_to_latest",
        ]

        for prompt_name in expected_prompts:
            assert prompt_name in mcp_prompts, f"Prompt '{prompt_name}' not registered"

    def test_prompt_count(self, mcp_prompts):
        """Test that exactly 6 prompts are registered."""
        assert len(mcp_prompts) == 6
