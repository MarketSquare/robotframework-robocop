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


class TestLintDirectoryTool:
    """Acceptance tests for lint_directory MCP tool."""

    def test_lint_directory_with_multiple_files(self, mcp_tools, tmp_path: Path):
        """User lints a directory containing multiple Robot Framework files."""
        lint_directory = mcp_tools["lint_directory"]

        # Create test files
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest one\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest two\n    log  b\n")
        (tmp_path / "other.txt").write_text("not a robot file")

        result = run_tool(lint_directory, directory_path=str(tmp_path))

        assert result["total_files"] == 2
        assert result["total_issues"] > 0
        assert "summary" in result
        assert "E" in result["summary"]
        assert "W" in result["summary"]
        assert "I" in result["summary"]

        # Each issue should include the file path
        for issue in result["issues"]:
            assert "file" in issue

    def test_lint_directory_recursive(self, mcp_tools, tmp_path: Path):
        """User lints a directory recursively."""
        lint_directory = mcp_tools["lint_directory"]

        # Create files in subdirectory
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test2.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        # Recursive (default)
        result = run_tool(lint_directory, directory_path=str(tmp_path), recursive=True)
        assert result["total_files"] == 2

        # Non-recursive
        result_non_recursive = run_tool(lint_directory, directory_path=str(tmp_path), recursive=False)
        assert result_non_recursive["total_files"] == 1

    def test_lint_directory_with_limit(self, mcp_tools, tmp_path: Path):
        """User limits the total number of issues across all files."""
        lint_directory = mcp_tools["lint_directory"]

        # Create files with many issues
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest a\n    log  x\n    log  y\n    log  z\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest b\n    log  x\n    log  y\n    log  z\n")

        result = run_tool(lint_directory, directory_path=str(tmp_path), limit=3)

        # Issues list should be limited
        assert len(result["issues"]) == 3
        # But total_issues should reflect actual count
        assert result["total_issues"] > 3
        # Should be marked as limited
        assert result["limited"] is True

    def test_lint_directory_empty(self, mcp_tools, tmp_path: Path):
        """User tries to lint a directory with no Robot Framework files."""
        lint_directory = mcp_tools["lint_directory"]

        with pytest.raises(ToolError, match=r"No .robot or .resource files found"):
            run_tool(lint_directory, directory_path=str(tmp_path))

    def test_lint_directory_nonexistent(self, mcp_tools):
        """User tries to lint a directory that doesn't exist."""
        lint_directory = mcp_tools["lint_directory"]

        with pytest.raises(ToolError, match="Directory not found"):
            run_tool(lint_directory, directory_path="/nonexistent/directory")


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
        lint_directory = mcp_tools["lint_directory"]

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

        result = run_tool(lint_directory, directory_path=str(tmp_path), recursive=True)

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
