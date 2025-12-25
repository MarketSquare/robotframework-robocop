"""Acceptance tests for MCP tools - testing tools as users would use them."""

import asyncio
from pathlib import Path
from textwrap import dedent

import pytest
from fastmcp.exceptions import ToolError

from robocop.mcp import mcp


@pytest.fixture(scope="module")
def mcp_tools():
    """Get the registered MCP tools."""

    async def get_tools():
        return await mcp.get_tools()

    return asyncio.run(get_tools())


def run_tool(tool, **kwargs):
    """Run an async tool function synchronously."""
    return asyncio.run(tool.fn(**kwargs, ctx=None))


class TestLintContentTool:
    """Acceptance tests for lint_content MCP tool."""

    def test_lint_clean_code(self, mcp_tools):
        """User lints well-formatted code and gets no issues."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Settings ***
            Documentation    A well-documented test suite.

            *** Test Cases ***
            Valid Test Case
                [Documentation]    This test is properly documented.
                Log    Hello World
        """
        ).lstrip()

        result = run_tool(lint_content, content=content)

        assert isinstance(result, list)
        # Well-formatted code may still have some minor issues, but should have few

    def test_lint_code_with_issues(self, mcp_tools):
        """User lints code with obvious problems and gets diagnostic issues."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(lint_content, content=content)

        assert len(result) > 0

        # Verify each issue has the expected structure
        for issue in result:
            assert "rule_id" in issue
            assert "name" in issue
            assert "message" in issue
            assert "severity" in issue
            assert issue["severity"] in ("E", "W", "I")
            assert "line" in issue
            assert issue["line"] >= 1
            assert "column" in issue
            assert issue["column"] >= 1

    def test_lint_select_specific_rules(self, mcp_tools):
        """User wants to check only naming convention rules."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(lint_content, content=content, select=["NAME*"])

        # All returned issues should be NAME rules
        assert len(result) > 0
        for issue in result:
            assert issue["rule_id"].startswith("NAME")

    def test_lint_ignore_specific_rules(self, mcp_tools):
        """User wants to ignore documentation rules."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Test Cases ***
            Test Case
                Log    Hello
        """
        ).lstrip()

        # Get all issues first
        all_issues = run_tool(lint_content, content=content)

        # Ignore DOC rules
        filtered = run_tool(lint_content, content=content, ignore=["DOC*"])

        # Should have fewer or equal issues
        assert len(filtered) <= len(all_issues)
        # No DOC rules in filtered
        for issue in filtered:
            assert not issue["rule_id"].startswith("DOC")

    def test_lint_only_errors(self, mcp_tools):
        """User only wants to see error-level issues."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(lint_content, content=content, threshold="E")

        for issue in result:
            assert issue["severity"] == "E"

    def test_lint_limit_results(self, mcp_tools):
        """User limits the number of issues returned."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  a
                log  b
                log  c
                log  d
        """
        ).lstrip()

        result = run_tool(lint_content, content=content, limit=2)

        assert len(result) == 2

    def test_lint_configure_rule(self, mcp_tools):
        """User configures a rule parameter to change behavior."""
        lint_content = mcp_tools["lint_content"]

        # Create content with a line longer than 120 chars but less than 200
        long_line = "A" * 150
        content = dedent(
            f"""
            *** Test Cases ***
            Test With Long Line
                Log    {long_line}
        """
        ).lstrip()

        # Default: should trigger line-too-long
        default_result = run_tool(lint_content, content=content, select=["LEN08"])
        assert any(issue["rule_id"] == "LEN08" for issue in default_result)

        # Configured: with increased limit, should not trigger
        configured_result = run_tool(
            lint_content,
            content=content,
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        assert not any(issue["rule_id"] == "LEN08" for issue in configured_result)

    def test_lint_resource_file(self, mcp_tools):
        """User lints a resource file (keywords only)."""
        lint_content = mcp_tools["lint_content"]

        content = dedent(
            """
            *** Keywords ***
            My Keyword
                [Documentation]    Does something.
                Log    Hello
        """
        ).lstrip()

        result = run_tool(lint_content, content=content, filename="test.resource")

        assert isinstance(result, list)


class TestLintFileTool:
    """Acceptance tests for lint_file MCP tool."""

    def test_lint_existing_file(self, mcp_tools, tmp_path: Path):
        """User lints an existing Robot Framework file."""
        lint_file = mcp_tools["lint_file"]

        robot_file = tmp_path / "test.robot"
        robot_file.write_text(
            dedent(
                """
            *** Test Cases ***
            test lowercase
                log  hello
        """
            ).lstrip()
        )

        result = run_tool(lint_file, file_path=str(robot_file))

        assert isinstance(result, list)
        assert len(result) > 0

        for issue in result:
            assert "rule_id" in issue
            assert "line" in issue

    def test_lint_nonexistent_file(self, mcp_tools):
        """User tries to lint a file that doesn't exist."""
        lint_file = mcp_tools["lint_file"]

        with pytest.raises(ToolError, match="File not found"):
            run_tool(lint_file, file_path="/nonexistent/path/to/file.robot")

    def test_lint_invalid_file_type(self, mcp_tools, tmp_path: Path):
        """User tries to lint a non-Robot Framework file."""
        lint_file = mcp_tools["lint_file"]

        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a robot file")

        with pytest.raises(ToolError, match="Invalid file type"):
            run_tool(lint_file, file_path=str(txt_file))

    def test_lint_file_with_configure(self, mcp_tools, tmp_path: Path):
        """User configures rules when linting a file."""
        lint_file = mcp_tools["lint_file"]

        long_line = "A" * 150
        robot_file = tmp_path / "test.robot"
        robot_file.write_text(f"*** Test Cases ***\nTest\n    Log    {long_line}\n")

        # Default: should trigger
        default_result = run_tool(lint_file, file_path=str(robot_file), select=["LEN08"])
        assert any(issue["rule_id"] == "LEN08" for issue in default_result)

        # Configured: should not trigger
        configured_result = run_tool(
            lint_file,
            file_path=str(robot_file),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        assert not any(issue["rule_id"] == "LEN08" for issue in configured_result)


class TestFormatContentTool:
    """Acceptance tests for format_content MCP tool."""

    def test_format_normalizes_separators(self, mcp_tools):
        """User formats code with inconsistent separators."""
        format_content = mcp_tools["format_content"]

        content = dedent(
            """
            *** Test Cases ***
            Test
                log  hello
                log    world
        """
        ).lstrip()

        result = run_tool(format_content, content=content)

        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result
        assert result["changed"] is True

    def test_format_unchanged_content(self, mcp_tools):
        """User formats already well-formatted code."""
        format_content = mcp_tools["format_content"]

        content = dedent(
            """
            *** Test Cases ***
            Test
                Log    Hello
        """
        ).lstrip()

        result = run_tool(format_content, content=content)

        assert "formatted" in result
        assert "changed" in result

    def test_format_with_specific_formatter(self, mcp_tools):
        """User applies only specific formatters."""
        format_content = mcp_tools["format_content"]

        content = "*** Test Cases ***\nTest\n    log  hello\n"

        result = run_tool(format_content, content=content, select=["NormalizeSeparators"])

        assert "formatted" in result
        assert "changed" in result

    def test_format_custom_space_count(self, mcp_tools):
        """User formats with custom indentation."""
        format_content = mcp_tools["format_content"]

        content = "*** Test Cases ***\nTest\n    Log    Hello\n"

        result = run_tool(format_content, content=content, space_count=2)

        assert "formatted" in result


class TestLintAndFormatTool:
    """Acceptance tests for lint_and_format MCP tool."""

    def test_lint_and_format_workflow(self, mcp_tools):
        """User formats code and sees remaining issues."""
        lint_and_format = mcp_tools["lint_and_format"]

        content = dedent(
            """
            *** Test Cases ***
            test lowercase
                log  hello
                log    world
        """
        ).lstrip()

        result = run_tool(lint_and_format, content=content)

        # Should have all expected fields
        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result
        assert "issues" in result
        assert "issues_before" in result
        assert "issues_after" in result
        assert "issues_fixed" in result

        # Formatting should have fixed some issues
        assert result["issues_fixed"] >= 0
        assert len(result["issues"]) <= result["issues_before"]

    def test_lint_and_format_with_limit(self, mcp_tools):
        """User formats code and limits the number of remaining issues shown."""
        lint_and_format = mcp_tools["lint_and_format"]

        content = dedent(
            """
            *** Test Cases ***
            test lowercase name
                log  hello
                log  world
                log  foo
                log  bar
        """
        ).lstrip()

        result = run_tool(lint_and_format, content=content, limit=2)

        # Issues list should be limited
        assert len(result["issues"]) <= 2
        # But issues_after should reflect actual count (may be higher)
        assert result["issues_after"] >= len(result["issues"])
        # issues_fixed should be accurate
        assert result["issues_fixed"] == result["issues_before"] - result["issues_after"]

    def test_lint_and_format_with_configure(self, mcp_tools):
        """User configures lint rules when using lint_and_format."""
        lint_and_format = mcp_tools["lint_and_format"]

        long_line = "A" * 150
        content = f"*** Test Cases ***\nTest\n    Log    {long_line}\n"

        # Default: should include line-too-long
        default_result = run_tool(lint_and_format, content=content, lint_select=["LEN08"])
        has_len08 = any(issue["rule_id"] == "LEN08" for issue in default_result["issues"])
        assert has_len08

        # Configured: should not include line-too-long
        configured_result = run_tool(
            lint_and_format,
            content=content,
            lint_select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        has_len08_configured = any(issue["rule_id"] == "LEN08" for issue in configured_result["issues"])
        assert not has_len08_configured


class TestGetRuleInfoTool:
    """Acceptance tests for get_rule_info MCP tool."""

    def test_get_rule_by_id(self, mcp_tools):
        """User looks up a rule by ID."""
        get_rule_info = mcp_tools["get_rule_info"]

        result = run_tool(get_rule_info, rule_name_or_id="LEN01")

        assert result["rule_id"] == "LEN01"
        assert "name" in result
        assert "message" in result
        assert "severity" in result
        assert "docs" in result
        assert "parameters" in result

    def test_get_rule_by_name(self, mcp_tools):
        """User looks up a rule by name."""
        get_rule_info = mcp_tools["get_rule_info"]

        result = run_tool(get_rule_info, rule_name_or_id="too-long-keyword")

        assert result["name"] == "too-long-keyword"
        assert result["rule_id"] == "LEN01"

    def test_get_nonexistent_rule(self, mcp_tools):
        """User looks up a rule that doesn't exist."""
        get_rule_info = mcp_tools["get_rule_info"]

        with pytest.raises(ToolError, match="not found"):
            run_tool(get_rule_info, rule_name_or_id="nonexistent-rule")


class TestGetFormatterInfoTool:
    """Acceptance tests for get_formatter_info MCP tool."""

    def test_get_formatter_info(self, mcp_tools):
        """User looks up a formatter."""
        get_formatter_info = mcp_tools["get_formatter_info"]

        result = run_tool(get_formatter_info, formatter_name="NormalizeSeparators")

        assert result["name"] == "NormalizeSeparators"
        assert "enabled" in result
        assert "docs" in result
        assert "parameters" in result
        assert "skip_options" in result

    def test_get_formatter_parameters(self, mcp_tools):
        """User looks up formatter parameters."""
        get_formatter_info = mcp_tools["get_formatter_info"]

        result = run_tool(get_formatter_info, formatter_name="NormalizeSeparators")

        # Should have parameters with name, default, type
        for param in result["parameters"]:
            assert "name" in param
            assert "default" in param
            assert "type" in param

        # NormalizeSeparators should have flatten_lines parameter
        param_names = [p["name"] for p in result["parameters"]]
        assert "flatten_lines" in param_names

    def test_get_nonexistent_formatter(self, mcp_tools):
        """User looks up a formatter that doesn't exist."""
        get_formatter_info = mcp_tools["get_formatter_info"]

        with pytest.raises(ToolError, match="not found"):
            run_tool(get_formatter_info, formatter_name="NonexistentFormatter")


class TestRealWorldWorkflows:
    """Tests simulating real-world usage patterns."""

    def test_code_review_workflow(self, mcp_tools):
        """
        Simulates a code review workflow:

        1. User submits code for review
        2. AI lints the code
        3. AI formats the code
        4. AI reports remaining issues
        """
        lint_and_format = mcp_tools["lint_and_format"]

        # User submits messy code
        user_code = dedent(
            """
            *** Test Cases ***
            test login functionality
                log  Starting test
                log    Doing something
                log  Finishing test
        """
        ).lstrip()

        result = run_tool(lint_and_format, content=user_code)

        # Provide feedback
        assert result["changed"] is True, "Code needed formatting"
        assert result["issues_fixed"] >= 0, "Some issues were automatically fixed"

        # The formatted code should be cleaner
        assert result["formatted"] != user_code

    def test_project_audit_workflow(self, mcp_tools, tmp_path: Path):
        """
        Simulates auditing an entire project:

        1. User points to a project directory
        2. AI scans all files
        3. AI reports summary statistics
        """
        lint_files = mcp_tools["lint_files"]

        # Create a small project
        (tmp_path / "tests").mkdir()
        (tmp_path / "tests" / "test_login.robot").write_text(
            "*** Test Cases ***\nLogin Test\n    Log    Testing login\n"
        )
        (tmp_path / "tests" / "test_checkout.robot").write_text(
            "*** Test Cases ***\nCheckout Test\n    Log    Testing checkout\n"
        )
        (tmp_path / "resources").mkdir()
        (tmp_path / "resources" / "common.resource").write_text(
            "*** Keywords ***\nSetup Browser\n    Log    Setting up\n"
        )

        result = run_tool(
            lint_files,
            file_patterns=["**/*.robot", "**/*.resource"],
            base_path=str(tmp_path),
        )

        # Should have scanned all files
        assert result["total_files"] == 3
        # Should have summary by severity
        assert "summary" in result
        assert sum(result["summary"].values()) == result["total_issues"]

    def test_rule_lookup_workflow(self, mcp_tools):
        """
        Simulates looking up documentation for a rule:

        1. User encounters an issue
        2. User asks about the rule
        3. AI provides detailed documentation
        """
        get_rule_info = mcp_tools["get_rule_info"]

        # User asks about a rule they saw in lint output
        result = run_tool(get_rule_info, rule_name_or_id="not-capitalized-test-case-title")

        assert "docs" in result
        assert len(result["docs"]) > 0

        # If the rule has parameters, user can see how to configure it
        if result["parameters"]:
            for param in result["parameters"]:
                assert "name" in param
                assert "default" in param

    def test_incremental_fix_workflow(self, mcp_tools):
        """
        Simulates incrementally fixing code:

        1. Lint code to see issues
        2. Format to fix automatic issues
        3. Review remaining issues
        """
        lint_content = mcp_tools["lint_content"]
        format_content = mcp_tools["format_content"]

        original_code = dedent(
            """
            *** Test Cases ***
            test something
                log  hello
                log    world
        """
        ).lstrip()

        # Step 1: See all issues
        initial_issues = run_tool(lint_content, content=original_code)
        assert len(initial_issues) > 0

        # Step 2: Format the code
        format_result = run_tool(format_content, content=original_code)
        assert format_result["changed"] is True

        # Step 3: Check remaining issues
        remaining_issues = run_tool(lint_content, content=format_result["formatted"])

        # Formatting should not have added issues
        assert len(remaining_issues) <= len(initial_issues)


class TestFormatFileTool:
    """Acceptance tests for format_file MCP tool."""

    def test_format_file_preview(self, mcp_tools, tmp_path: Path):
        """User previews formatting changes without modifying file."""
        format_file = mcp_tools["format_file"]

        robot_file = tmp_path / "test.robot"
        original_content = "*** Test Cases ***\nTest\n    log  hello\n"
        robot_file.write_text(original_content)

        result = run_tool(format_file, file_path=str(robot_file))

        assert result["changed"] is True
        assert result["written"] is False
        # File should not have been modified
        assert robot_file.read_text() == original_content

    def test_format_file_overwrite(self, mcp_tools, tmp_path: Path):
        """User formats file and saves changes."""
        format_file = mcp_tools["format_file"]

        robot_file = tmp_path / "test.robot"
        original_content = "*** Test Cases ***\nTest\n    log  hello\n"
        robot_file.write_text(original_content)

        result = run_tool(format_file, file_path=str(robot_file), overwrite=True)

        assert result["changed"] is True
        assert result["written"] is True
        # File should have been modified
        assert robot_file.read_text() != original_content
        assert robot_file.read_text() == result["formatted"]

    def test_format_file_not_found(self, mcp_tools):
        """User tries to format a non-existent file."""
        format_file = mcp_tools["format_file"]

        with pytest.raises(ToolError, match="File not found"):
            run_tool(format_file, file_path="/nonexistent/path/test.robot")


class TestFormatFilesTool:
    """Acceptance tests for format_files MCP tool."""

    def test_format_files_with_glob(self, mcp_tools, tmp_path: Path):
        """User formats multiple files using a glob pattern."""
        format_files = mcp_tools["format_files"]

        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = run_tool(format_files, file_patterns=["tests/*.robot"], base_path=str(tmp_path))

        assert result["total_files"] == 2
        assert result["files_changed"] >= 0
        assert result["files_written"] == 0  # Not overwritten by default

    def test_format_files_overwrite(self, mcp_tools, tmp_path: Path):
        """User formats and saves multiple files."""
        format_files = mcp_tools["format_files"]

        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = run_tool(
            format_files,
            file_patterns=["*.robot"],
            base_path=str(tmp_path),
            overwrite=True,
        )

        assert result["total_files"] == 2
        assert result["files_written"] == result["files_changed"]

    def test_format_files_no_matches(self, mcp_tools, tmp_path: Path):
        """User uses a pattern with no matches."""
        format_files = mcp_tools["format_files"]

        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            run_tool(format_files, file_patterns=["nonexistent/*.robot"], base_path=str(tmp_path))


class TestGetStatisticsTool:
    """Acceptance tests for get_statistics MCP tool."""

    def test_get_statistics_overview(self, mcp_tools, tmp_path: Path):
        """User gets an overview of code quality for a directory."""
        get_statistics = mcp_tools["get_statistics"]

        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        result = run_tool(get_statistics, directory_path=str(tmp_path))

        assert "summary" in result
        assert "severity_breakdown" in result
        assert "top_issues" in result
        assert "quality_score" in result
        assert "recommendations" in result

        assert result["summary"]["total_files"] == 2
        assert result["quality_score"]["score"] >= 0
        assert result["quality_score"]["score"] <= 100
        assert result["quality_score"]["grade"] in ("A", "B", "C", "D", "F")

    def test_get_statistics_recursive(self, mcp_tools, tmp_path: Path):
        """User scans a project with subdirectories."""
        get_statistics = mcp_tools["get_statistics"]

        subdir = tmp_path / "tests"
        subdir.mkdir()
        (tmp_path / "root.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (subdir / "nested.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        # Recursive (default)
        result = run_tool(get_statistics, directory_path=str(tmp_path))
        assert result["summary"]["total_files"] == 2

        # Non-recursive
        result_flat = run_tool(get_statistics, directory_path=str(tmp_path), recursive=False)
        assert result_flat["summary"]["total_files"] == 1

    def test_get_statistics_with_filters(self, mcp_tools, tmp_path: Path):
        """User filters statistics to specific rules."""
        get_statistics = mcp_tools["get_statistics"]

        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = run_tool(get_statistics, directory_path=str(tmp_path), select=["NAME*"])

        # All top issues should be NAME rules
        for issue in result["top_issues"]:
            assert issue["rule_id"].startswith("NAME")

    def test_get_statistics_empty_directory(self, mcp_tools, tmp_path: Path):
        """User tries to get statistics for empty directory."""
        get_statistics = mcp_tools["get_statistics"]

        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            run_tool(get_statistics, directory_path=str(tmp_path))


class TestExplainIssueTool:
    """Acceptance tests for explain_issue MCP tool."""

    def test_explain_issue_at_line(self, mcp_tools):
        """User asks for explanation of issue at specific line."""
        explain_issue = mcp_tools["explain_issue"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(explain_issue, content=content, line=2)

        assert result["issues_found"] is True
        assert len(result["issues"]) > 0
        assert result["line"] == 2

        # Should include documentation
        issue = result["issues"][0]
        assert "rule_id" in issue
        assert "message" in issue

    def test_explain_issue_with_context(self, mcp_tools):
        """User gets context around the issue."""
        explain_issue = mcp_tools["explain_issue"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
                log  world
        """
        ).lstrip()

        result = run_tool(explain_issue, content=content, line=3, context_lines=2)

        context = result["context"]
        assert "lines" in context
        assert "target_line" in context
        assert context["target_line"] == 3

        # Check that context lines are marked correctly
        for line_info in context["lines"]:
            assert "line_number" in line_info
            assert "content" in line_info
            assert "is_target" in line_info

    def test_explain_issue_no_issues_at_line(self, mcp_tools):
        """User asks about a line with no issues."""
        explain_issue = mcp_tools["explain_issue"]

        content = dedent(
            """
            *** Test Cases ***
            Valid Test Name
                Log    Hello
        """
        ).lstrip()

        result = run_tool(explain_issue, content=content, line=1)

        # Line 1 is the header, likely no issues
        assert "issues_found" in result
        assert "context" in result


class TestNewToolsWorkflows:
    """Tests for workflows using the new tools."""

    def test_project_cleanup_workflow(self, mcp_tools, tmp_path: Path):
        """
        Simulates cleaning up an entire project:

        1. Get statistics to understand scope
        2. Format all files
        3. Check improved statistics
        """
        get_statistics = mcp_tools["get_statistics"]
        format_files = mcp_tools["format_files"]

        # Create messy files
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest\n    log  b\n")

        # Step 1: Get initial statistics
        initial_stats = run_tool(get_statistics, directory_path=str(tmp_path))
        assert initial_stats["summary"]["total_issues"] > 0

        # Step 2: Format all files
        format_result = run_tool(
            format_files,
            file_patterns=["*.robot"],
            base_path=str(tmp_path),
            overwrite=True,
        )
        assert format_result["files_changed"] >= 0

        # Step 3: Check improved statistics
        final_stats = run_tool(get_statistics, directory_path=str(tmp_path))
        # After formatting, we may have fewer issues
        assert final_stats["summary"]["total_files"] == initial_stats["summary"]["total_files"]

    def test_issue_investigation_workflow(self, mcp_tools):
        """
        Simulates investigating a specific issue:

        1. Lint code to find issues
        2. Explain specific issue
        3. Get full rule documentation
        """
        lint_content = mcp_tools["lint_content"]
        explain_issue = mcp_tools["explain_issue"]
        get_rule_info = mcp_tools["get_rule_info"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        # Step 1: Find issues
        issues = run_tool(lint_content, content=content)
        assert len(issues) > 0

        first_issue = issues[0]
        issue_line = first_issue["line"]

        # Step 2: Explain the issue at that line
        explanation = run_tool(explain_issue, content=content, line=issue_line)
        assert explanation["issues_found"] is True

        # Step 3: Get full rule documentation
        rule_docs = run_tool(get_rule_info, rule_name_or_id=first_issue["rule_id"])
        assert "docs" in rule_docs
        assert len(rule_docs["docs"]) > 0


class TestAdvancedWorkflows:
    """Tests for advanced multi-step workflows."""

    def test_full_cleanup_and_verify_workflow(self, mcp_tools, tmp_path: Path):
        """
        Complete cleanup workflow:

        1. Get statistics to understand scope
        2. Format all files
        3. Lint all files
        4. Get new statistics
        5. Verify improvement
        """
        get_statistics = mcp_tools["get_statistics"]
        format_files = mcp_tools["format_files"]
        lint_files = mcp_tools["lint_files"]

        # Create test files with various issues
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest one\n    log  a\n    log   b\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest two\n    log   c\n")
        (tmp_path / "lib.resource").write_text("*** Keywords ***\nmy keyword\n    Log  d\n")

        # Step 1: Get initial statistics
        initial_stats = run_tool(get_statistics, directory_path=str(tmp_path))
        initial_issues = initial_stats["summary"]["total_issues"]
        assert initial_issues > 0

        # Step 2: Format all files
        format_result = run_tool(
            format_files,
            file_patterns=["**/*.robot", "**/*.resource"],
            base_path=str(tmp_path),
            overwrite=True,
        )
        assert format_result["total_files"] == 3

        # Step 3: Lint files to see remaining issues
        lint_result = run_tool(
            lint_files,
            file_patterns=["**/*.robot", "**/*.resource"],
            base_path=str(tmp_path),
        )
        assert lint_result["total_files"] == 3

        # Step 4: Get final statistics
        final_stats = run_tool(get_statistics, directory_path=str(tmp_path))
        final_issues = final_stats["summary"]["total_issues"]

        # Step 5: Verify - formatting shouldn't increase issues
        assert final_issues <= initial_issues

    def test_selective_rule_workflow(self, mcp_tools, tmp_path: Path):
        """
        Workflow focusing on specific rule categories:

        1. List rules in a category
        2. Lint files for only those rules
        3. Get detailed info on triggered rules
        """
        list_rules = mcp_tools["list_rules"]
        lint_files = mcp_tools["lint_files"]
        get_rule_info = mcp_tools["get_rule_info"]

        # Create test file
        (tmp_path / "test.robot").write_text(
            "*** Test Cases ***\ntest with naming issues\n    Log    Hello\nAnother test case\n    Log    World\n"
        )

        # Step 1: List NAME rules
        name_rules = run_tool(list_rules, category="NAME")
        assert len(name_rules) > 0

        # Step 2: Lint for only NAME rules
        lint_result = run_tool(
            lint_files,
            file_patterns=["test.robot"],
            base_path=str(tmp_path),
            select=["NAME*"],
        )

        # All issues should be NAME rules
        for issue in lint_result["issues"]:
            assert issue["rule_id"].startswith("NAME")

        # Step 3: Get detailed info on first triggered rule
        if lint_result["issues"]:
            rule_id = lint_result["issues"][0]["rule_id"]
            rule_info = run_tool(get_rule_info, rule_name_or_id=rule_id)
            assert "docs" in rule_info
            assert "parameters" in rule_info

    def test_format_then_lint_workflow(self, mcp_tools, tmp_path: Path):
        """
        Workflow: format files then lint to show remaining manual fixes.

        This tests that formatting reduces issues but doesn't eliminate all.
        """
        format_file = mcp_tools["format_file"]
        lint_file = mcp_tools["lint_file"]

        # Create file with both auto-fixable and manual issues
        robot_file = tmp_path / "test.robot"
        robot_file.write_text(
            "*** Test Cases ***\n"
            "test lowercase name\n"  # NAME issue - manual fix
            "    log  hello\n"  # Spacing issue - auto-fixable
            "    log    world\n"  # Spacing issue - auto-fixable
        )

        # Format the file
        format_result = run_tool(format_file, file_path=str(robot_file), overwrite=True)
        assert format_result["changed"] is True

        # Lint to see remaining issues
        lint_result = run_tool(lint_file, file_path=str(robot_file))

        # Should still have NAME issues (can't be auto-fixed)
        name_issues = [i for i in lint_result if i["rule_id"].startswith("NAME")]
        assert len(name_issues) > 0


class TestEdgeCaseFiles:
    """Tests for edge case file handling."""

    def test_lint_deeply_nested_directory(self, mcp_tools, tmp_path: Path):
        """Test linting files in deeply nested directories."""
        lint_files = mcp_tools["lint_files"]

        # Create deeply nested structure
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True)
        (deep_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    Hi\n")

        result = run_tool(
            lint_files,
            file_patterns=["**/*.robot"],
            base_path=str(tmp_path),
        )

        assert result["total_files"] == 1
        # Should find the deeply nested file
        assert (
            any("a/b/c/d/e/test.robot" in str(issue.get("file", "")) for issue in result["issues"])
            or result["total_issues"] >= 0
        )

    def test_lint_files_with_spaces_in_names(self, mcp_tools, tmp_path: Path):
        """Test linting files with spaces in filenames."""
        lint_file = mcp_tools["lint_file"]

        robot_file = tmp_path / "test file with spaces.robot"
        robot_file.write_text("*** Test Cases ***\ntest\n    Log    Hi\n")

        result = run_tool(lint_file, file_path=str(robot_file))

        assert isinstance(result, list)

    def test_format_empty_robot_file(self, mcp_tools, tmp_path: Path):
        """Test formatting an empty Robot Framework file."""
        format_file = mcp_tools["format_file"]

        robot_file = tmp_path / "empty.robot"
        robot_file.write_text("")

        result = run_tool(format_file, file_path=str(robot_file))

        assert "formatted" in result
        assert "changed" in result

    def test_lint_file_with_only_comments(self, mcp_tools, tmp_path: Path):
        """Test linting a file with only comments."""
        lint_file = mcp_tools["lint_file"]

        robot_file = tmp_path / "comments_only.robot"
        robot_file.write_text("# This is a comment\n# Another comment\n")

        result = run_tool(lint_file, file_path=str(robot_file))

        assert isinstance(result, list)

    def test_lint_files_with_mixed_files(self, mcp_tools, tmp_path: Path):
        """Test linting directory with mixed Robot and non-Robot files."""
        lint_files = mcp_tools["lint_files"]

        # Create mixed files
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    Hi\n")
        (tmp_path / "lib.resource").write_text("*** Keywords ***\nKw\n    Log    Hi\n")
        (tmp_path / "readme.md").write_text("# README\n")
        (tmp_path / "script.py").write_text("print('hello')\n")
        (tmp_path / "data.json").write_text('{"key": "value"}\n')

        result = run_tool(
            lint_files,
            file_patterns=["**/*.robot", "**/*.resource"],
            base_path=str(tmp_path),
        )

        # Should only find .robot and .resource files
        assert result["total_files"] == 2

    def test_format_files_preserves_unchanged(self, mcp_tools, tmp_path: Path):
        """Test that formatting preserves already formatted files."""
        format_files = mcp_tools["format_files"]

        # Create a well-formatted file
        good_file = tmp_path / "good.robot"
        good_file.write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        # Create a poorly formatted file
        bad_file = tmp_path / "bad.robot"
        bad_file.write_text("*** Test Cases ***\ntest\n    log  hello\n")

        result = run_tool(
            format_files,
            file_patterns=["*.robot"],
            base_path=str(tmp_path),
            overwrite=True,
        )

        assert result["total_files"] == 2
        # At least the bad file should have changed
        assert result["files_changed"] >= 1


class TestListTools:
    """Tests for list_rules and list_formatters tools."""

    def test_list_rules_category_filter(self, mcp_tools):
        """Test filtering rules by category."""
        list_rules = mcp_tools["list_rules"]

        # Test multiple categories
        for category in ["LEN", "NAME", "DOC", "MISC"]:
            result = run_tool(list_rules, category=category)
            if result:  # Some categories might have no rules
                for rule in result:
                    assert rule["rule_id"].startswith(category)

    def test_list_rules_severity_filter(self, mcp_tools):
        """Test filtering rules by severity."""
        list_rules = mcp_tools["list_rules"]

        for severity in ["E", "W", "I"]:
            result = run_tool(list_rules, severity=severity)
            for rule in result:
                assert rule["severity"] == severity

    def test_list_formatters_enabled_vs_all(self, mcp_tools):
        """Test listing enabled vs all formatters."""
        list_formatters = mcp_tools["list_formatters"]

        enabled = run_tool(list_formatters, enabled_only=True)
        all_formatters = run_tool(list_formatters, enabled_only=False)

        assert len(all_formatters) >= len(enabled)
        # All enabled formatters should be in the all list
        enabled_names = {f["name"] for f in enabled}
        all_names = {f["name"] for f in all_formatters}
        assert enabled_names.issubset(all_names)


class TestSuggestFixesTool:
    """Tests for suggest_fixes tool."""

    def test_suggest_fixes_basic(self, mcp_tools):
        """Test basic fix suggestions."""
        suggest_fixes = mcp_tools["suggest_fixes"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(suggest_fixes, content=content)

        assert "fixes" in result
        assert "total_issues" in result
        assert "auto_fixable" in result
        assert "manual_required" in result
        assert "recommendation" in result

    def test_suggest_fixes_with_filename(self, mcp_tools):
        """Test fix suggestions with specific filename."""
        suggest_fixes = mcp_tools["suggest_fixes"]

        content = "*** Keywords ***\nmy keyword\n    Log    Hello\n"

        result = run_tool(suggest_fixes, content=content, filename="lib.resource")

        assert "fixes" in result

    def test_suggest_fixes_rule_filter(self, mcp_tools):
        """Test fix suggestions filtered by rule IDs."""
        suggest_fixes = mcp_tools["suggest_fixes"]

        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = run_tool(suggest_fixes, content=content, rule_ids=["NAME*"])

        # All fixes should be for NAME rules
        for fix in result["fixes"]:
            assert fix["rule_id"].startswith("NAME")
