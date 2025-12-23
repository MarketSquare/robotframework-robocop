"""Tests for MCP tools."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pytest
from fastmcp.exceptions import ToolError

from robocop.mcp.tools import (
    _collect_robot_files,
    _format_content_impl,
    _get_formatter_info_impl,
    _get_rule_info_impl,
    _lint_content_impl,
    _lint_file_impl,
)


class TestLintContent:
    """Tests for lint_content tool."""

    def test_lint_valid_content(self):
        """Test linting valid Robot Framework content."""
        content = """*** Test Cases ***
Valid Test
    Log    Hello World
"""
        result = _lint_content_impl(content)
        assert isinstance(result, list)

    def test_lint_content_with_issues(self):
        """Test linting content with issues."""
        content = """*** Test Cases ***
test without capital
    log  hello
"""
        result = _lint_content_impl(content)
        assert len(result) > 0
        # Check structure of returned diagnostics
        for diag in result:
            assert "rule_id" in diag
            assert "name" in diag
            assert "message" in diag
            assert "severity" in diag
            assert "line" in diag
            assert "column" in diag

    def test_lint_with_select(self):
        """Test linting with specific rules selected."""
        content = """*** Test Cases ***
Very Long Test Case Name That Should Trigger Length Rule
    Log    Hello
"""
        # Only select length rules
        result = _lint_content_impl(content, select=["LEN*"])
        # Should only get LEN rules
        for diag in result:
            assert diag["rule_id"].startswith("LEN")

    def test_lint_with_ignore(self):
        """Test linting with rules ignored."""
        content = """*** Test Cases ***
test without capital
    log  hello
"""
        # Get all issues
        all_issues = _lint_content_impl(content)

        # Ignore NAME rules
        filtered = _lint_content_impl(content, ignore=["NAME*"])
        # Should have fewer issues
        assert len(filtered) <= len(all_issues)
        # No NAME rules in filtered
        for diag in filtered:
            assert not diag["rule_id"].startswith("NAME")

    def test_lint_with_threshold(self):
        """Test linting with severity threshold."""
        content = """*** Test Cases ***
test without capital
    log  hello
"""
        # Get all issues
        all_issues = _lint_content_impl(content, threshold="I")

        # Only errors
        errors_only = _lint_content_impl(content, threshold="E")
        assert len(errors_only) <= len(all_issues)
        for diag in errors_only:
            assert diag["severity"] == "E"

    def test_lint_with_limit(self):
        """Test linting with issue count limit."""
        content = """*** Test Cases ***
test without capital
    log  hello
    log  world
    log  foo
"""
        # Get all issues
        all_issues = _lint_content_impl(content)
        assert len(all_issues) >= 3  # Should have multiple issues

        # Limit to 2 issues
        limited = _lint_content_impl(content, limit=2)
        assert len(limited) == 2

        # Limit to 1 issue
        single = _lint_content_impl(content, limit=1)
        assert len(single) == 1

        # Limit higher than actual issues should return all
        high_limit = _lint_content_impl(content, limit=100)
        assert len(high_limit) == len(all_issues)


class TestFormatContent:
    """Tests for format_content tool."""

    def test_format_content_normalizes_separators(self):
        """Test that formatting normalizes separators."""
        content = """*** Test Cases ***
Test
    log  hello
    log    world
"""
        result = _format_content_impl(content)
        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result

        # Should have normalized the separators
        assert result["changed"] is True

    def test_format_unchanged_content(self):
        """Test formatting already formatted content."""
        content = """*** Test Cases ***
Test
    Log    Hello
"""
        result = _format_content_impl(content)
        # May or may not change depending on default formatters
        assert "formatted" in result
        assert "changed" in result


class TestGetRuleInfo:
    """Tests for get_rule_info tool."""

    def test_get_rule_by_id(self):
        """Test getting rule info by ID."""
        result = _get_rule_info_impl("LEN01")
        assert result["rule_id"] == "LEN01"
        assert "name" in result
        assert "message" in result
        assert "severity" in result
        assert "docs" in result
        assert "parameters" in result

    def test_get_rule_by_name(self):
        """Test getting rule info by name."""
        result = _get_rule_info_impl("too-long-keyword")
        assert result["name"] == "too-long-keyword"
        assert result["rule_id"] == "LEN01"

    def test_get_nonexistent_rule(self):
        """Test getting info for nonexistent rule."""
        with pytest.raises(ToolError, match="not found"):
            _get_rule_info_impl("nonexistent-rule")


class TestGetFormatterInfo:
    """Tests for get_formatter_info tool."""

    def test_get_formatter_info(self):
        """Test getting formatter info."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert result["name"] == "NormalizeSeparators"
        assert "enabled" in result
        assert "docs" in result

    def test_get_nonexistent_formatter(self):
        """Test getting info for nonexistent formatter."""
        with pytest.raises(ToolError, match="not found"):
            _get_formatter_info_impl("NonexistentFormatter")


class TestLintDirectory:
    """Tests for lint_directory helper functions."""

    def test_collect_robot_files(self):
        """Test collecting Robot Framework files from directory."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create test files
            (tmppath / "test1.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
            (tmppath / "test2.resource").write_text("*** Keywords ***\nKw\n    Log    Hi\n")
            (tmppath / "other.txt").write_text("not a robot file")

            # Create subdirectory with files
            subdir = tmppath / "subdir"
            subdir.mkdir()
            (subdir / "test3.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

            # Test recursive
            files = _collect_robot_files(tmppath, recursive=True)
            assert len(files) == 3

            # Test non-recursive
            files = _collect_robot_files(tmppath, recursive=False)
            assert len(files) == 2

    def test_collect_robot_files_empty(self):
        """Test collecting files from empty directory."""
        with TemporaryDirectory() as tmpdir:
            files = _collect_robot_files(Path(tmpdir))
            assert files == []

    def test_lint_file_with_file_in_result(self):
        """Test that lint_file can include file path in results."""
        with TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            robot_file = tmppath / "test.robot"
            robot_file.write_text("*** Test Cases ***\ntest lowercase\n    log  hi\n")

            # Without file in result
            result = _lint_file_impl(str(robot_file), include_file_in_result=False)
            assert "file" not in result[0]

            # With file in result
            result = _lint_file_impl(str(robot_file), include_file_in_result=True)
            assert "file" in result[0]
            assert result[0]["file"] == str(robot_file)
