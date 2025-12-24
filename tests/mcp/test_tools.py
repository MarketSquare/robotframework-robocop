"""Tests for MCP tools."""

from pathlib import Path
from textwrap import dedent

import pytest
from fastmcp.exceptions import ToolError

from robocop.formatter.formatters.NormalizeSeparators import NormalizeSeparators
from robocop.mcp.tools import (
    _collect_robot_files,
    _expand_file_patterns,
    _explain_issue_impl,
    _format_content_impl,
    _format_file_impl,
    _format_files_impl,
    _generate_recommendations,
    _get_formatter_info_impl,
    _get_formatter_parameters,
    _get_line_context,
    _get_rule_info_impl,
    _get_statistics_impl,
    _group_issues,
    _is_glob_pattern,
    _lint_content_impl,
    _lint_file_impl,
    _lint_files_impl,
    _list_formatters_impl,
    _list_rules_impl,
    _suggest_fixes_impl,
)


class TestLintContent:
    """Tests for lint_content tool."""

    def test_lint_valid_content(self):
        """Test linting valid Robot Framework content."""
        content = dedent(
            """
            *** Test Cases ***
            Valid Test
                Log    Hello World
        """
        ).lstrip()
        result = _lint_content_impl(content)
        assert isinstance(result, list)

    def test_lint_content_with_issues(self):
        """Test linting content with issues."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
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
        content = dedent(
            """
            *** Test Cases ***
            Very Long Test Case Name That Should Trigger Length Rule
                Log    Hello
        """
        ).lstrip()
        # Only select length rules
        result = _lint_content_impl(content, select=["LEN*"])
        # Should only get LEN rules
        for diag in result:
            assert diag["rule_id"].startswith("LEN")

    def test_lint_with_ignore(self):
        """Test linting with rules ignored."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
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
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
        # Get all issues
        all_issues = _lint_content_impl(content, threshold="I")

        # Only errors
        errors_only = _lint_content_impl(content, threshold="E")
        assert len(errors_only) <= len(all_issues)
        for diag in errors_only:
            assert diag["severity"] == "E"

    def test_lint_with_limit(self):
        """Test linting with issue count limit."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
                log  world
                log  foo
        """
        ).lstrip()
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
        content = dedent(
            """
            *** Test Cases ***
            Test
                log  hello
                log    world
        """
        ).lstrip()
        result = _format_content_impl(content)
        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result

        # Should have normalized the separators
        assert result["changed"] is True

    def test_format_unchanged_content(self):
        """Test formatting already formatted content."""
        content = dedent(
            """
            *** Test Cases ***
            Test
                Log    Hello
        """
        ).lstrip()
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
        content = dedent(
            f"""
            *** Test Cases ***
            Test With Long Line
                Log    {long_line}
        """
        ).lstrip()

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


class TestLintFileErrors:
    """Tests for lint_file error handling."""

    def test_lint_file_not_found(self):
        """Test linting a file that doesn't exist."""
        with pytest.raises(ToolError, match="File not found"):
            _lint_file_impl("/nonexistent/path/to/file.robot")

    def test_lint_file_invalid_extension(self, tmp_path: Path):
        """Test linting a file with invalid extension."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a robot file")

        with pytest.raises(ToolError, match="Invalid file type"):
            _lint_file_impl(str(txt_file))

    def test_lint_file_with_limit(self, tmp_path: Path):
        """Test linting a file with limit parameter."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\ntest lowercase\n    log  a\n    log  b\n    log  c\n    log  d\n")

        # Get all issues
        all_issues = _lint_file_impl(str(robot_file))
        assert len(all_issues) >= 2

        # Limit to 1 issue
        limited = _lint_file_impl(str(robot_file), limit=1)
        assert len(limited) == 1

    def test_lint_file_with_configure(self, tmp_path: Path):
        """Test linting a file with configure parameter."""
        # Create a file with a long line
        long_line = "A" * 150
        robot_file = tmp_path / "test.robot"
        robot_file.write_text(f"*** Test Cases ***\nTest\n    Log    {long_line}\n")

        # Without configuration, should trigger line-too-long
        result_default = _lint_file_impl(str(robot_file), select=["LEN08"])
        has_line_too_long = any(d["rule_id"] == "LEN08" for d in result_default)
        assert has_line_too_long

        # With configuration to allow longer lines
        result_configured = _lint_file_impl(
            str(robot_file),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        has_line_too_long_configured = any(d["rule_id"] == "LEN08" for d in result_configured)
        assert not has_line_too_long_configured


class TestLintContentErrors:
    """Tests for lint_content error handling."""

    def test_lint_with_invalid_threshold(self):
        """Test linting with invalid threshold raises error."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        with pytest.raises(ToolError, match="Invalid threshold"):
            _lint_content_impl(content, threshold="X")

    def test_lint_resource_file(self):
        """Test linting content as a resource file."""
        content = "*** Keywords ***\nMy Keyword\n    Log    Hello\n"
        result = _lint_content_impl(content, filename="test.resource")
        assert isinstance(result, list)


class TestFormatContentErrors:
    """Tests for format_content error handling."""

    def test_format_with_select(self):
        """Test formatting with specific formatters selected."""
        content = "*** Test Cases ***\nTest\n    log  hello\n"
        result = _format_content_impl(content, select=["NormalizeSeparators"])
        assert "formatted" in result
        assert "changed" in result

    def test_format_with_custom_space_count(self):
        """Test formatting with custom space count."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        result = _format_content_impl(content, space_count=2)
        assert "formatted" in result

    def test_format_with_custom_line_length(self):
        """Test formatting with custom line length."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        result = _format_content_impl(content, line_length=80)
        assert "formatted" in result


class TestLintAndFormatIntegration:
    """Integration tests for lint_and_format functionality."""

    def test_lint_and_format_fixes_issues(self):
        """Test that formatting can fix some linting issues."""
        # Content with inconsistent separators
        content = dedent(
            """
            *** Test Cases ***
            Test
                log  hello
                log    world
        """
        ).lstrip()

        # Get issues before formatting
        issues_before = _lint_content_impl(content)

        # Format the content
        format_result = _format_content_impl(content)
        assert format_result["changed"] is True

        # Get issues after formatting
        issues_after = _lint_content_impl(format_result["formatted"])

        # Formatting should have fixed some issues or at least not made it worse
        assert isinstance(issues_before, list)
        assert isinstance(issues_after, list)
        assert len(issues_after) <= len(issues_before)

    def test_lint_and_format_with_limit_accurate_counts(self):
        """Test that lint_and_format returns accurate counts even with limit."""
        # Content with multiple issues
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
        # Get full issue count
        issues_before_full = _lint_content_impl(content)
        format_result = _format_content_impl(content)
        issues_after_full = _lint_content_impl(format_result["formatted"])

        # The counts should be accurate regardless of any limit
        issues_fixed = len(issues_before_full) - len(issues_after_full)
        assert issues_fixed >= 0  # Formatting shouldn't add issues


class TestListRules:
    """Tests for list_rules tool."""

    def test_list_all_rules(self):
        """Test listing all rules."""
        result = _list_rules_impl()
        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        for rule in result:
            assert "rule_id" in rule
            assert "name" in rule
            assert "severity" in rule
            assert "enabled" in rule
            assert "message" in rule

    def test_list_rules_by_category(self):
        """Test filtering rules by category."""
        result = _list_rules_impl(category="LEN")
        assert len(result) > 0
        for rule in result:
            assert rule["rule_id"].startswith("LEN")

    def test_list_rules_by_severity(self):
        """Test filtering rules by severity."""
        result = _list_rules_impl(severity="W")
        assert len(result) > 0
        for rule in result:
            assert rule["severity"] == "W"

    def test_list_rules_enabled_only(self):
        """Test filtering to enabled rules only."""
        all_rules = _list_rules_impl()
        enabled_rules = _list_rules_impl(enabled_only=True)

        # Should have fewer or equal rules
        assert len(enabled_rules) <= len(all_rules)

        # All should be enabled
        for rule in enabled_rules:
            assert rule["enabled"] is True

    def test_list_rules_combined_filters(self):
        """Test combining multiple filters."""
        result = _list_rules_impl(category="NAME", severity="W", enabled_only=True)
        for rule in result:
            assert rule["rule_id"].startswith("NAME")
            assert rule["severity"] == "W"
            assert rule["enabled"] is True

    def test_list_rules_sorted_by_id(self):
        """Test that rules are sorted by ID."""
        result = _list_rules_impl()
        rule_ids = [r["rule_id"] for r in result]
        assert rule_ids == sorted(rule_ids)


class TestListFormatters:
    """Tests for list_formatters tool."""

    def test_list_enabled_formatters(self):
        """Test listing enabled formatters (default)."""
        result = _list_formatters_impl()
        assert isinstance(result, list)
        assert len(result) > 0

        # Check structure
        for formatter in result:
            assert "name" in formatter
            assert "enabled" in formatter
            assert "description" in formatter

    def test_list_all_formatters(self):
        """Test listing all formatters including disabled."""
        enabled = _list_formatters_impl(enabled_only=True)
        all_formatters = _list_formatters_impl(enabled_only=False)

        # Should have more or equal formatters
        assert len(all_formatters) >= len(enabled)

    def test_list_formatters_sorted_by_name(self):
        """Test that formatters are sorted by name."""
        result = _list_formatters_impl(enabled_only=False)
        names = [f["name"] for f in result]
        assert names == sorted(names)

    def test_list_formatters_has_normalize_separators(self):
        """Test that NormalizeSeparators is in the list."""
        result = _list_formatters_impl(enabled_only=False)
        names = [f["name"] for f in result]
        assert "NormalizeSeparators" in names


class TestSuggestFixes:
    """Tests for suggest_fixes tool."""

    def test_suggest_fixes_basic(self):
        """Test basic fix suggestions."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
        result = _suggest_fixes_impl(content)

        assert "fixes" in result
        assert "total_issues" in result
        assert "auto_fixable" in result
        assert "manual_required" in result
        assert "recommendation" in result

        assert result["total_issues"] == len(result["fixes"])
        assert result["auto_fixable"] + result["manual_required"] == result["total_issues"]

    def test_suggest_fixes_structure(self):
        """Test fix suggestion structure."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
        result = _suggest_fixes_impl(content)

        for fix in result["fixes"]:
            assert "rule_id" in fix
            assert "name" in fix
            assert "line" in fix
            assert "message" in fix
            assert "suggestion" in fix
            assert "auto_fixable" in fix

    def test_suggest_fixes_with_rule_filter(self):
        """Test fix suggestions filtered by rule IDs."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()
        # Only get NAME rule suggestions
        result = _suggest_fixes_impl(content, rule_ids=["NAME*"])

        for fix in result["fixes"]:
            assert fix["rule_id"].startswith("NAME")

    def test_suggest_fixes_no_issues(self):
        """Test fix suggestions for clean code."""
        content = dedent(
            """
            *** Test Cases ***
            Valid Test Case
                Log    Hello World
        """
        ).lstrip()
        result = _suggest_fixes_impl(content)

        # May still have some minor issues, but structure should be correct
        assert "fixes" in result
        assert "total_issues" in result

    def test_suggest_fixes_recommendation(self):
        """Test that recommendation is appropriate."""
        # Content with auto-fixable issues (spacing)
        content = dedent(
            """
            *** Test Cases ***
            Test
                Log  Hello
        """
        ).lstrip()
        result = _suggest_fixes_impl(content)

        # Recommendation should exist
        assert isinstance(result["recommendation"], str)
        assert len(result["recommendation"]) > 0


class TestIsGlobPattern:
    """Tests for _is_glob_pattern helper."""

    def test_glob_patterns(self):
        """Test that glob patterns are detected."""
        assert _is_glob_pattern("*.robot") is True
        assert _is_glob_pattern("tests/**/*.robot") is True
        assert _is_glob_pattern("test?.robot") is True
        assert _is_glob_pattern("test[0-9].robot") is True

    def test_non_glob_patterns(self):
        """Test that non-glob patterns are not detected as globs."""
        assert _is_glob_pattern("test.robot") is False
        assert _is_glob_pattern("/path/to/test.robot") is False
        assert _is_glob_pattern("tests/login.robot") is False


class TestExpandFilePatterns:
    """Tests for _expand_file_patterns helper."""

    def test_explicit_paths(self, tmp_path: Path):
        """Test expanding explicit file paths."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, unmatched = _expand_file_patterns(["test1.robot", "test2.robot"], tmp_path)
        assert len(files) == 2
        assert unmatched == []

    def test_glob_patterns(self, tmp_path: Path):
        """Test expanding glob patterns."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, unmatched = _expand_file_patterns(["tests/*.robot"], tmp_path)
        assert len(files) == 2
        assert unmatched == []

    def test_recursive_glob(self, tmp_path: Path):
        """Test recursive glob patterns."""
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)
        (deep / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, unmatched = _expand_file_patterns(["**/*.robot"], tmp_path)
        assert len(files) == 1
        assert unmatched == []

    def test_mixed_patterns(self, tmp_path: Path):
        """Test mixing explicit paths and globs."""
        (tmp_path / "explicit.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "pattern.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, unmatched = _expand_file_patterns(["explicit.robot", "tests/*.robot"], tmp_path)
        assert len(files) == 2
        assert unmatched == []

    def test_deduplication(self, tmp_path: Path):
        """Test that same file matched multiple times is deduplicated."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, _unmatched = _expand_file_patterns(["test.robot", "*.robot", "test.robot"], tmp_path)
        assert len(files) == 1

    def test_filters_non_robot_files(self, tmp_path: Path):
        """Test that non-Robot files are filtered out."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (tmp_path / "test.txt").write_text("not robot")
        (tmp_path / "test.py").write_text("not robot")

        files, _unmatched = _expand_file_patterns(["*"], tmp_path)
        assert len(files) == 1
        assert files[0].suffix == ".robot"

    def test_unmatched_patterns(self, tmp_path: Path):
        """Test that unmatched patterns are tracked."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, unmatched = _expand_file_patterns(
            ["test.robot", "nonexistent.robot", "nofiles/*.robot"],
            tmp_path,
        )
        assert len(files) == 1
        assert "nonexistent.robot" in unmatched
        assert "nofiles/*.robot" in unmatched

    def test_absolute_paths(self, tmp_path: Path):
        """Test handling absolute paths."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        files, _unmatched = _expand_file_patterns(
            [str(tmp_path / "test.robot")],
            Path("/different/base"),
        )
        assert len(files) == 1

    def test_resource_files_included(self, tmp_path: Path):
        """Test that .resource files are included."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    Log    Hi\n")
        (tmp_path / "lib.resource").write_text("*** Keywords ***\nKw\n    Log    Hi\n")

        files, _unmatched = _expand_file_patterns(["*"], tmp_path)
        assert len(files) == 2

    def test_empty_patterns(self, tmp_path: Path):
        """Test with empty patterns list."""
        files, unmatched = _expand_file_patterns([], tmp_path)
        assert files == []
        assert unmatched == []


class TestLintFilesImpl:
    """Tests for _lint_files_impl function."""

    def test_lint_multiple_files(self, tmp_path: Path):
        """Test linting multiple specific files."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest a\n    Log    x\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest b\n    Log    y\n")

        result = _lint_files_impl(["test1.robot", "test2.robot"], str(tmp_path))

        assert result["total_files"] == 2
        assert result["total_issues"] > 0
        assert "summary" in result
        assert result["unmatched_patterns"] == []

    def test_lint_with_glob(self, tmp_path: Path):
        """Test linting with glob pattern."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\ntest\n    Log    y\n")

        result = _lint_files_impl(["tests/*.robot"], str(tmp_path))

        assert result["total_files"] == 2

    def test_lint_with_limit(self, tmp_path: Path):
        """Test limiting results."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    a\n    Log    b\n")

        # Get all issues first
        all_result = _lint_files_impl(["test.robot"], str(tmp_path))

        if all_result["total_issues"] > 1:
            # Limit to 1 issue
            result = _lint_files_impl(["test.robot"], str(tmp_path), limit=1)
            assert len(result["issues"]) == 1
            assert result["total_issues"] > 1
            assert result["limited"] is True

    def test_lint_with_select(self, tmp_path: Path):
        """Test selecting specific rules."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest lowercase\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), select=["NAME*"])

        for issue in result["issues"]:
            assert issue["rule_id"].startswith("NAME")

    def test_no_files_raises_error(self, tmp_path: Path):
        """Test that no matching files raises ToolError."""
        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            _lint_files_impl(["nonexistent.robot"], str(tmp_path))

    def test_includes_file_path(self, tmp_path: Path):
        """Test that issues include file path."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        for issue in result["issues"]:
            assert "file" in issue

    def test_summary_counts(self, tmp_path: Path):
        """Test that summary counts are correct."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        assert "summary" in result
        assert "E" in result["summary"]
        assert "W" in result["summary"]
        assert "I" in result["summary"]
        # Sum of summary should equal total issues
        summary_total = sum(result["summary"].values())
        assert summary_total == result["total_issues"]

    def test_files_with_issues_count(self, tmp_path: Path):
        """Test files_with_issues count."""
        # File with issues
        (tmp_path / "bad.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        # File without issues (proper formatting)
        (tmp_path / "good.robot").write_text("*** Test Cases ***\nValid Test\n    Log    Hello\n")

        result = _lint_files_impl(["bad.robot", "good.robot"], str(tmp_path))

        assert result["total_files"] == 2
        # At least one file should have issues
        assert result["files_with_issues"] >= 1

    def test_unmatched_patterns_in_result(self, tmp_path: Path):
        """Test that unmatched patterns are included in result."""
        (tmp_path / "exists.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["exists.robot", "missing.robot"], str(tmp_path))

        assert result["total_files"] == 1
        assert "missing.robot" in result["unmatched_patterns"]

    def test_with_configure(self, tmp_path: Path):
        """Test linting with configure parameter."""
        long_line = "A" * 150
        (tmp_path / "test.robot").write_text(f"*** Test Cases ***\nTest\n    Log    {long_line}\n")

        # Without configuration, should trigger line-too-long
        result_default = _lint_files_impl(["test.robot"], str(tmp_path), select=["LEN08"])
        has_line_too_long = any(d["rule_id"] == "LEN08" for d in result_default["issues"])
        assert has_line_too_long

        # With configuration to allow longer lines
        result_configured = _lint_files_impl(
            ["test.robot"],
            str(tmp_path),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        has_line_too_long_configured = any(d["rule_id"] == "LEN08" for d in result_configured["issues"])
        assert not has_line_too_long_configured


class TestGroupIssues:
    """Tests for _group_issues function."""

    def test_group_by_severity(self):
        """Test grouping issues by severity."""
        issues = [
            {"rule_id": "LEN01", "severity": "W", "file": "a.robot"},
            {"rule_id": "NAME01", "severity": "E", "file": "b.robot"},
            {"rule_id": "DOC01", "severity": "I", "file": "a.robot"},
            {"rule_id": "LEN02", "severity": "W", "file": "c.robot"},
        ]

        grouped, counts = _group_issues(issues, "severity")

        assert "E" in grouped
        assert "W" in grouped
        assert "I" in grouped
        assert len(grouped["E"]) == 1
        assert len(grouped["W"]) == 2
        assert len(grouped["I"]) == 1
        assert counts == {"E": 1, "W": 2, "I": 1}

    def test_group_by_rule(self):
        """Test grouping issues by rule ID."""
        issues = [
            {"rule_id": "LEN01", "severity": "W", "file": "a.robot"},
            {"rule_id": "LEN01", "severity": "W", "file": "b.robot"},
            {"rule_id": "NAME01", "severity": "E", "file": "a.robot"},
        ]

        grouped, counts = _group_issues(issues, "rule")

        assert "LEN01" in grouped
        assert "NAME01" in grouped
        assert len(grouped["LEN01"]) == 2
        assert len(grouped["NAME01"]) == 1
        assert counts == {"LEN01": 2, "NAME01": 1}

    def test_group_by_file(self):
        """Test grouping issues by file path."""
        issues = [
            {"rule_id": "LEN01", "severity": "W", "file": "/path/a.robot"},
            {"rule_id": "NAME01", "severity": "E", "file": "/path/a.robot"},
            {"rule_id": "DOC01", "severity": "I", "file": "/path/b.robot"},
        ]

        grouped, counts = _group_issues(issues, "file")

        assert "/path/a.robot" in grouped
        assert "/path/b.robot" in grouped
        assert len(grouped["/path/a.robot"]) == 2
        assert len(grouped["/path/b.robot"]) == 1
        assert counts == {"/path/a.robot": 2, "/path/b.robot": 1}

    def test_limit_per_group(self):
        """Test that limit applies per group."""
        issues = [
            {"rule_id": "LEN01", "severity": "W", "file": "a.robot"},
            {"rule_id": "LEN01", "severity": "W", "file": "b.robot"},
            {"rule_id": "LEN01", "severity": "W", "file": "c.robot"},
            {"rule_id": "NAME01", "severity": "E", "file": "a.robot"},
            {"rule_id": "NAME01", "severity": "E", "file": "b.robot"},
        ]

        grouped, counts = _group_issues(issues, "rule", limit_per_group=2)

        # Should only have 2 issues per rule in grouped
        assert len(grouped["LEN01"]) == 2
        assert len(grouped["NAME01"]) == 2
        # But counts should reflect total
        assert counts == {"LEN01": 3, "NAME01": 2}

    def test_empty_issues(self):
        """Test with empty issues list."""
        grouped, counts = _group_issues([], "severity")

        assert grouped == {}
        assert counts == {}

    def test_invalid_group_by_raises_error(self):
        """Test that invalid group_by raises ToolError."""
        issues = [{"rule_id": "LEN01", "severity": "W", "file": "a.robot"}]

        with pytest.raises(ToolError, match="Invalid group_by"):
            _group_issues(issues, "invalid")

    def test_missing_field_uses_unknown(self):
        """Test that missing field uses 'unknown' as key."""
        issues = [
            {"rule_id": "LEN01", "severity": "W"},  # missing 'file'
        ]

        grouped, _counts = _group_issues(issues, "file")

        assert "unknown" in grouped
        assert len(grouped["unknown"]) == 1


class TestLintFilesImplGroupBy:
    """Tests for _lint_files_impl with group_by parameter."""

    def test_group_by_severity(self, tmp_path: Path):
        """Test _lint_files_impl with group_by='severity'."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), group_by="severity")

        assert isinstance(result["issues"], dict)
        assert "group_counts" in result
        # Issues should be grouped by severity
        for key in result["issues"]:
            assert key in ("E", "W", "I")

    def test_group_by_rule(self, tmp_path: Path):
        """Test _lint_files_impl with group_by='rule'."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), group_by="rule")

        assert isinstance(result["issues"], dict)
        assert "group_counts" in result
        # All keys should be rule IDs
        for key in result["issues"]:
            assert len(key) >= 3  # Rule IDs are at least 3 chars

    def test_group_by_with_limit(self, tmp_path: Path):
        """Test that limit applies per group when group_by is set."""
        # Create file with multiple issues
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n    Log    y\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), group_by="rule", limit=1)

        # Each group should have at most 1 issue
        for issues in result["issues"].values():
            assert len(issues) <= 1
        # Check if limited flag is set when any group was limited
        if any(result["group_counts"][k] > 1 for k in result["group_counts"]):
            assert result["limited"] is True

    def test_no_group_by_returns_list(self, tmp_path: Path):
        """Test that without group_by, issues is a list (not dict)."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        assert isinstance(result["issues"], list)
        assert "group_counts" not in result


class TestFormatFile:
    """Tests for format_file tool."""

    def test_format_file_basic(self, tmp_path: Path):
        """Test formatting a file without overwriting."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    log  hello\n")

        result = _format_file_impl(str(robot_file))

        assert "file" in result
        assert "formatted" in result
        assert "changed" in result
        assert "diff" in result
        assert "written" in result
        assert result["changed"] is True
        assert result["written"] is False  # Not overwritten by default

    def test_format_file_overwrite(self, tmp_path: Path):
        """Test formatting a file with overwrite=True."""
        robot_file = tmp_path / "test.robot"
        original_content = "*** Test Cases ***\nTest\n    log  hello\n"
        robot_file.write_text(original_content)

        result = _format_file_impl(str(robot_file), overwrite=True)

        assert result["changed"] is True
        assert result["written"] is True
        # Verify file was actually modified
        new_content = robot_file.read_text()
        assert new_content != original_content
        assert new_content == result["formatted"]

    def test_format_file_unchanged(self, tmp_path: Path):
        """Test formatting an already formatted file."""
        robot_file = tmp_path / "test.robot"
        # Well-formatted content
        robot_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        result = _format_file_impl(str(robot_file), overwrite=True)

        # May or may not change depending on default formatters
        assert "formatted" in result
        if not result["changed"]:
            assert result["written"] is False

    def test_format_file_not_found(self):
        """Test formatting a non-existent file."""
        with pytest.raises(ToolError, match="File not found"):
            _format_file_impl("/nonexistent/path/test.robot")

    def test_format_file_invalid_extension(self, tmp_path: Path):
        """Test formatting a file with invalid extension."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("some content")

        with pytest.raises(ToolError, match="Invalid file type"):
            _format_file_impl(str(txt_file))

    def test_format_file_with_select(self, tmp_path: Path):
        """Test formatting with specific formatters."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    log  hello\n")

        result = _format_file_impl(str(robot_file), select=["NormalizeSeparators"])

        assert "formatted" in result

    def test_format_file_custom_space_count(self, tmp_path: Path):
        """Test formatting with custom space count."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        result = _format_file_impl(str(robot_file), space_count=2)

        assert "formatted" in result

    def test_format_resource_file(self, tmp_path: Path):
        """Test formatting a .resource file."""
        resource_file = tmp_path / "lib.resource"
        resource_file.write_text("*** Keywords ***\nMy Keyword\n    log  hi\n")

        result = _format_file_impl(str(resource_file))

        assert "formatted" in result
        assert result["file"] == str(resource_file)


class TestFormatFiles:
    """Tests for format_files tool."""

    def test_format_multiple_files(self, tmp_path: Path):
        """Test formatting multiple files."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["test1.robot", "test2.robot"], str(tmp_path))

        assert result["total_files"] == 2
        assert "files_changed" in result
        assert "files_unchanged" in result
        assert "files_written" in result
        assert result["files_written"] == 0  # Not overwritten by default
        assert len(result["results"]) == 2

    def test_format_files_with_overwrite(self, tmp_path: Path):
        """Test formatting files with overwrite."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["test1.robot", "test2.robot"], str(tmp_path), overwrite=True)

        assert result["files_written"] == result["files_changed"]

    def test_format_files_with_glob(self, tmp_path: Path):
        """Test formatting with glob pattern."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["tests/*.robot"], str(tmp_path))

        assert result["total_files"] == 2

    def test_format_files_recursive_glob(self, tmp_path: Path):
        """Test formatting with recursive glob pattern."""
        deep = tmp_path / "a" / "b"
        deep.mkdir(parents=True)
        (deep / "test.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["**/*.robot"], str(tmp_path))

        assert result["total_files"] == 1

    def test_format_files_no_matches(self, tmp_path: Path):
        """Test formatting with no matching files."""
        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            _format_files_impl(["nonexistent.robot"], str(tmp_path))

    def test_format_files_unmatched_patterns(self, tmp_path: Path):
        """Test that unmatched patterns are tracked."""
        (tmp_path / "exists.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["exists.robot", "missing.robot"], str(tmp_path))

        assert result["total_files"] == 1
        assert "missing.robot" in result["unmatched_patterns"]

    def test_format_files_results_structure(self, tmp_path: Path):
        """Test the structure of per-file results."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["test.robot"], str(tmp_path))

        for file_result in result["results"]:
            assert "file" in file_result
            assert "changed" in file_result
            assert "written" in file_result


class TestGetStatistics:
    """Tests for get_statistics tool."""

    def test_get_statistics_basic(self, tmp_path: Path):
        """Test basic statistics gathering."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        result = _get_statistics_impl(str(tmp_path))

        assert "directory" in result
        assert "summary" in result
        assert "severity_breakdown" in result
        assert "top_issues" in result
        assert "quality_score" in result
        assert "recommendations" in result

    def test_get_statistics_summary(self, tmp_path: Path):
        """Test statistics summary structure."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        summary = result["summary"]
        assert "total_files" in summary
        assert "files_with_issues" in summary
        assert "files_clean" in summary
        assert "total_issues" in summary
        assert "avg_issues_per_file" in summary
        assert "max_issues_in_file" in summary

        assert summary["total_files"] == 1

    def test_get_statistics_severity_breakdown(self, tmp_path: Path):
        """Test severity breakdown in statistics."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        severity = result["severity_breakdown"]
        assert "E" in severity
        assert "W" in severity
        assert "I" in severity
        # Sum should equal total issues
        total = severity["E"] + severity["W"] + severity["I"]
        assert total == result["summary"]["total_issues"]

    def test_get_statistics_quality_score(self, tmp_path: Path):
        """Test quality score structure."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        result = _get_statistics_impl(str(tmp_path))

        quality = result["quality_score"]
        assert "score" in quality
        assert "grade" in quality
        assert "label" in quality
        assert 0 <= quality["score"] <= 100
        assert quality["grade"] in ("A", "B", "C", "D", "F")

    def test_get_statistics_top_issues(self, tmp_path: Path):
        """Test top issues list."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        assert isinstance(result["top_issues"], list)
        for issue in result["top_issues"]:
            assert "rule_id" in issue
            assert "count" in issue
            assert issue["count"] > 0

    def test_get_statistics_recommendations(self, tmp_path: Path):
        """Test recommendations list."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        assert isinstance(result["recommendations"], list)
        assert len(result["recommendations"]) > 0
        for rec in result["recommendations"]:
            assert isinstance(rec, str)

    def test_get_statistics_recursive(self, tmp_path: Path):
        """Test recursive directory scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  a\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\ntest\n    log  b\n")

        # Recursive (default)
        result_recursive = _get_statistics_impl(str(tmp_path), recursive=True)
        assert result_recursive["summary"]["total_files"] == 2

        # Non-recursive
        result_nonrecursive = _get_statistics_impl(str(tmp_path), recursive=False)
        assert result_nonrecursive["summary"]["total_files"] == 1

    def test_get_statistics_with_select(self, tmp_path: Path):
        """Test statistics with rule selection."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path), select=["NAME*"])

        # All issues should be NAME rules
        for issue in result["top_issues"]:
            assert issue["rule_id"].startswith("NAME")

    def test_get_statistics_directory_not_found(self):
        """Test statistics for non-existent directory."""
        with pytest.raises(ToolError, match="Directory not found"):
            _get_statistics_impl("/nonexistent/path")

    def test_get_statistics_not_directory(self, tmp_path: Path):
        """Test statistics for a file instead of directory."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    Log    Hi\n")

        with pytest.raises(ToolError, match="Not a directory"):
            _get_statistics_impl(str(robot_file))

    def test_get_statistics_empty_directory(self, tmp_path: Path):
        """Test statistics for empty directory."""
        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            _get_statistics_impl(str(tmp_path))


class TestGenerateRecommendations:
    """Tests for _generate_recommendations helper."""

    def test_recommendations_for_errors(self):
        """Test recommendations when errors are present."""
        severity_counts = {"E": 5, "W": 2, "I": 1}
        top_rules = [("LEN01", 3), ("NAME01", 2)]

        result = _generate_recommendations(severity_counts, top_rules, 70)

        # Should recommend fixing errors first
        assert any("error" in rec.lower() for rec in result)

    def test_recommendations_for_common_rule(self):
        """Test recommendations when a rule appears many times."""
        severity_counts = {"E": 0, "W": 10, "I": 0}
        top_rules = [("LEN01", 10)]

        result = _generate_recommendations(severity_counts, top_rules, 50)

        # Should mention the common rule
        assert any("LEN01" in rec for rec in result)

    def test_recommendations_for_low_quality(self):
        """Test recommendations for low quality score."""
        severity_counts = {"E": 0, "W": 5, "I": 5}
        top_rules = [("DOC01", 3)]

        result = _generate_recommendations(severity_counts, top_rules, 50)

        # Should recommend formatter
        assert any("formatter" in rec.lower() for rec in result)

    def test_recommendations_for_good_quality(self):
        """Test recommendations for good quality code."""
        severity_counts = {"E": 0, "W": 0, "I": 0}
        top_rules = []

        result = _generate_recommendations(severity_counts, top_rules, 100)

        # Should have positive message
        assert len(result) > 0
        assert any("good" in rec.lower() for rec in result)


class TestExplainIssue:
    """Tests for explain_issue tool."""

    def test_explain_issue_basic(self):
        """Test basic issue explanation."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=2)

        assert "line" in result
        assert "issues_found" in result
        assert "context" in result
        assert result["line"] == 2

    def test_explain_issue_with_issues(self):
        """Test explanation when issues are found."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=2)

        assert result["issues_found"] is True
        assert "issues" in result
        assert len(result["issues"]) > 0

    def test_explain_issue_structure(self):
        """Test issue explanation structure."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=2)

        for issue in result["issues"]:
            assert "rule_id" in issue
            assert "name" in issue
            assert "message" in issue
            assert "severity" in issue
            assert "line" in issue
            assert "column" in issue

    def test_explain_issue_includes_documentation(self):
        """Test that explanation includes rule documentation."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=2)

        if result["issues"]:
            issue = result["issues"][0]
            # Should include additional context fields
            assert "why_it_matters" in issue or "full_documentation" in issue

    def test_explain_issue_no_issues_at_line(self):
        """Test explanation when no issues at specified line."""
        content = dedent(
            """
            *** Test Cases ***
            Valid Test Name
                Log    Hello
        """
        ).lstrip()

        # Line 1 is the settings header, no issues there
        result = _explain_issue_impl(content, line=1)

        # May or may not find issues depending on rules
        assert "issues_found" in result
        assert "context" in result

    def test_explain_issue_related_issues(self):
        """Test that related issues on nearby lines are included."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
                log  world
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=3)

        assert "related_issues" in result

    def test_explain_issue_context_lines(self):
        """Test custom context lines."""
        content = dedent(
            """
            *** Test Cases ***
            test without capital
                log  hello
                log  world
                log  foo
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=3, context_lines=1)

        context = result["context"]
        # Should have target line +/- 1 = at most 3 lines
        assert len(context["lines"]) <= 3

    def test_explain_issue_context_structure(self):
        """Test context structure."""
        content = dedent(
            """
            *** Test Cases ***
            Test
                Log    Hello
        """
        ).lstrip()

        result = _explain_issue_impl(content, line=2)

        context = result["context"]
        assert "lines" in context
        assert "target_line" in context
        assert "target_content" in context

        for line_info in context["lines"]:
            assert "line_number" in line_info
            assert "content" in line_info
            assert "is_target" in line_info


class TestGetLineContext:
    """Tests for _get_line_context helper."""

    def test_get_line_context_basic(self):
        """Test basic context extraction."""
        content = "line1\nline2\nline3\nline4\nline5"

        result = _get_line_context(content, line=3, context_lines=1)

        assert result["target_line"] == 3
        assert result["target_content"] == "line3"
        assert len(result["lines"]) == 3  # line 2, 3, 4

    def test_get_line_context_at_start(self):
        """Test context at start of file."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=1, context_lines=2)

        assert result["target_line"] == 1
        # Should only have lines after, not before
        assert len(result["lines"]) == 3  # line 1, 2, 3

    def test_get_line_context_at_end(self):
        """Test context at end of file."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=3, context_lines=2)

        assert result["target_line"] == 3
        # Should only have lines before, not after
        assert len(result["lines"]) == 3  # line 1, 2, 3

    def test_get_line_context_target_marked(self):
        """Test that target line is marked."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=2, context_lines=1)

        target_found = False
        for line_info in result["lines"]:
            if line_info["is_target"]:
                target_found = True
                assert line_info["line_number"] == 2
        assert target_found
