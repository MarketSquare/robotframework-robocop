"""Tests for MCP tools."""

from pathlib import Path
from textwrap import dedent

import pytest
from fastmcp.exceptions import ToolError

from robocop.formatter.formatters.NormalizeSeparators import NormalizeSeparators
from robocop.mcp.tools import (
    _collect_robot_files,
    _format_content_impl,
    _get_formatter_info_impl,
    _get_formatter_parameters,
    _get_rule_info_impl,
    _lint_content_impl,
    _lint_file_impl,
)


class TestLintContent:
    """Tests for lint_content tool."""

    def test_lint_valid_content(self):
        """Test linting valid Robot Framework content."""
        content = dedent("""
            *** Test Cases ***
            Valid Test
                Log    Hello World
        """).lstrip()
        result = _lint_content_impl(content)
        assert isinstance(result, list)

    def test_lint_content_with_issues(self):
        """Test linting content with issues."""
        content = dedent("""
            *** Test Cases ***
            test without capital
                log  hello
        """).lstrip()
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
        content = dedent("""
            *** Test Cases ***
            Very Long Test Case Name That Should Trigger Length Rule
                Log    Hello
        """).lstrip()
        # Only select length rules
        result = _lint_content_impl(content, select=["LEN*"])
        # Should only get LEN rules
        for diag in result:
            assert diag["rule_id"].startswith("LEN")

    def test_lint_with_ignore(self):
        """Test linting with rules ignored."""
        content = dedent("""
            *** Test Cases ***
            test without capital
                log  hello
        """).lstrip()
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
        content = dedent("""
            *** Test Cases ***
            test without capital
                log  hello
        """).lstrip()
        # Get all issues
        all_issues = _lint_content_impl(content, threshold="I")

        # Only errors
        errors_only = _lint_content_impl(content, threshold="E")
        assert len(errors_only) <= len(all_issues)
        for diag in errors_only:
            assert diag["severity"] == "E"

    def test_lint_with_limit(self):
        """Test linting with issue count limit."""
        content = dedent("""
            *** Test Cases ***
            test without capital
                log  hello
                log  world
                log  foo
        """).lstrip()
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
        content = dedent("""
            *** Test Cases ***
            Test
                log  hello
                log    world
        """).lstrip()
        result = _format_content_impl(content)
        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result

        # Should have normalized the separators
        assert result["changed"] is True

    def test_format_unchanged_content(self):
        """Test formatting already formatted content."""
        content = dedent("""
            *** Test Cases ***
            Test
                Log    Hello
        """).lstrip()
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

    def test_collect_robot_files(self, tmp_path: Path):
        """Test collecting Robot Framework files from directory."""
        # Create test files
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (tmp_path / "test2.resource").write_text("*** Keywords ***\nKw\n    Log    Hi\n")
        (tmp_path / "other.txt").write_text("not a robot file")

        # Create subdirectory with files
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "test3.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        # Test recursive
        files = _collect_robot_files(tmp_path, recursive=True)
        assert len(files) == 3

        # Test non-recursive
        files = _collect_robot_files(tmp_path, recursive=False)
        assert len(files) == 2

    def test_collect_robot_files_empty(self, tmp_path: Path):
        """Test collecting files from empty directory."""
        files = _collect_robot_files(tmp_path)
        assert files == []

    def test_lint_file_with_file_in_result(self, tmp_path: Path):
        """Test that lint_file can include file path in results."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\ntest lowercase\n    log  hi\n")

        # Without file in result
        result = _lint_file_impl(str(robot_file), include_file_in_result=False)
        assert "file" not in result[0]

        # With file in result
        result = _lint_file_impl(str(robot_file), include_file_in_result=True)
        assert "file" in result[0]
        assert result[0]["file"] == str(robot_file)


class TestLintContentConfigure:
    """Tests for lint_content with configure parameter."""

    def test_lint_with_configure(self):
        """Test linting with rule configuration."""
        # Content with a long line that would trigger line-too-long rule (LEN08)
        # Default limit is 120 chars, so we need a line longer than that
        long_line = "A" * 150
        content = dedent(f"""
            *** Test Cases ***
            Test With Long Line
                Log    {long_line}
        """).lstrip()

        # Without configuration, should trigger line-too-long (LEN08)
        result_default = _lint_content_impl(content, select=["LEN08"])
        has_line_too_long = any(d["rule_id"] == "LEN08" for d in result_default)
        assert has_line_too_long, "Should detect line-too-long with default config (120 chars)"

        # With configuration to allow longer lines, should not trigger
        result_configured = _lint_content_impl(content, select=["LEN08"], configure=["line-too-long.line_length=200"])
        has_line_too_long_configured = any(d["rule_id"] == "LEN08" for d in result_configured)
        assert not has_line_too_long_configured, "Should not detect line-too-long with increased limit"


class TestGetFormatterInfoParameters:
    """Tests for get_formatter_info with parameters."""

    def test_get_formatter_info_includes_parameters(self):
        """Test that formatter info includes parameters."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert "parameters" in result
        assert isinstance(result["parameters"], list)

        # NormalizeSeparators has flatten_lines and align_new_line parameters
        param_names = [p["name"] for p in result["parameters"]]
        assert "flatten_lines" in param_names
        assert "align_new_line" in param_names

    def test_get_formatter_info_includes_skip_options(self):
        """Test that formatter info includes skip options."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert "skip_options" in result
        assert isinstance(result["skip_options"], list)
        # NormalizeSeparators handles skip_documentation among others
        assert "skip_documentation" in result["skip_options"]

    def test_formatter_parameter_structure(self):
        """Test that formatter parameters have correct structure."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        for param in result["parameters"]:
            assert "name" in param
            assert "default" in param
            assert "type" in param

    def test_get_formatter_parameters_extracts_types(self):
        """Test that formatter parameters have correct types."""
        params = _get_formatter_parameters(NormalizeSeparators)
        param_dict = {p["name"]: p for p in params}

        # Check flatten_lines is bool with default False
        assert param_dict["flatten_lines"]["type"] == "bool"
        assert param_dict["flatten_lines"]["default"] is False

        # Check align_new_line is bool with default False
        assert param_dict["align_new_line"]["type"] == "bool"
        assert param_dict["align_new_line"]["default"] is False
