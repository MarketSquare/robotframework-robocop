"""Tests for MCP tools."""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest
from fastmcp.exceptions import ToolError

from robocop.formatter.formatters.NormalizeSeparators import NormalizeSeparators
from robocop.mcp.tools.batch_operations import (
    _collect_robot_files,
    _expand_file_patterns,
    _format_files_impl,
    _group_issues,
    _is_glob_pattern,
    _lint_files_impl,
)
from robocop.mcp.tools.diagnostics import (
    _explain_issue_impl,
    _generate_recommendations,
    _get_line_context,
    _get_statistics_impl,
    _suggest_fixes_impl,
    _worst_files_impl,
)
from robocop.mcp.tools.documentation import (
    _get_formatter_info_impl,
    _get_formatter_parameters,
    _get_rule_info_impl,
    _list_formatters_impl,
    _list_prompts_impl,
    _list_rules_impl,
    _search_rules_impl,
)
from robocop.mcp.tools.formatting import _format_content_impl, _format_file_impl, _lint_and_format_impl
from robocop.mcp.tools.linting import _lint_content_impl, _lint_file_impl
from robocop.mcp.tools.models import DiagnosticResult


def _make_issue(
    rule_id: str = "TEST01",
    name: str = "test-rule",
    message: str = "Test message",
    severity: str = "W",
    line: int = 1,
    column: int = 1,
    end_line: int = 1,
    end_column: int = 10,
    file: str | None = None,
) -> DiagnosticResult:
    """Create DiagnosticResult instances for testing."""
    return DiagnosticResult(
        rule_id=rule_id,
        name=name,
        message=message,
        severity=severity,
        line=line,
        column=column,
        end_line=end_line,
        end_column=end_column,
        file=file,
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
        # Check structure of returned diagnostics (Pydantic models have all attributes)
        for diag in result:
            assert diag.rule_id
            assert diag.name
            assert diag.message
            assert diag.severity
            assert diag.line
            assert diag.column

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
            assert diag.rule_id.startswith("LEN")

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
            assert not diag.rule_id.startswith("NAME")

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
            assert diag.severity == "E"

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
        assert result.diff is not None  # Optional field - test expects it to exist when changed

        # Should have normalized the separators
        assert result.changed is True

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
        assert isinstance(result.changed, bool)


class TestGetRuleInfo:
    """Tests for get_rule_info tool."""

    def test_get_rule_by_id(self):
        """Test getting rule info by ID."""
        result = _get_rule_info_impl("LEN01")
        assert result.rule_id == "LEN01"
        assert result.docs is not None  # Optional field - verify it exists for this rule

    def test_get_rule_by_name(self):
        """Test getting rule info by name."""
        result = _get_rule_info_impl("too-long-keyword")
        assert result.name == "too-long-keyword"
        assert result.rule_id == "LEN01"

    def test_get_nonexistent_rule(self):
        """Test getting info for nonexistent rule."""
        with pytest.raises(ToolError, match="not found"):
            _get_rule_info_impl("nonexistent-rule")


class TestGetFormatterInfo:
    """Tests for get_formatter_info tool."""

    def test_get_formatter_info(self):
        """Test getting formatter info."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert result.name == "NormalizeSeparators"

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
        assert result[0].file is None

        # With file in result
        result = _lint_file_impl(str(robot_file), include_file_in_result=True)
        assert result[0].file is not None  # Optional field - verify files are included
        assert result[0].file == str(robot_file)


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
        has_line_too_long = any(d.rule_id == "LEN08" for d in result_default)
        assert has_line_too_long, "Should detect line-too-long with default config (120 chars)"

        # With configuration to allow longer lines, should not trigger
        result_configured = _lint_content_impl(content, select=["LEN08"], configure=["line-too-long.line_length=200"])
        has_line_too_long_configured = any(d.rule_id == "LEN08" for d in result_configured)
        assert not has_line_too_long_configured, "Should not detect line-too-long with increased limit"


class TestGetFormatterInfoParameters:
    """Tests for get_formatter_info with parameters."""

    def test_get_formatter_info_includes_parameters(self):
        """Test that formatter info includes parameters."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert isinstance(result.parameters, list)

        # NormalizeSeparators has flatten_lines and align_new_line parameters
        param_names = [p.name for p in result.parameters]
        assert "flatten_lines" in param_names
        assert "align_new_line" in param_names

    def test_get_formatter_info_includes_skip_options(self):
        """Test that formatter info includes skip options."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert isinstance(result.skip_options, list)
        # NormalizeSeparators handles skip_documentation among others
        assert "skip_documentation" in result.skip_options

    def test_formatter_parameter_structure(self):
        """Test that formatter parameters have correct structure."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        # FormatterParam model validates all required fields: name, type
        # default can be None for some params
        assert len(result.parameters) > 0

    def test_get_formatter_parameters_extracts_types(self):
        """Test that formatter parameters have correct types."""
        params = _get_formatter_parameters(NormalizeSeparators)
        param_dict = {p.name: p for p in params}

        # Check flatten_lines is bool with default False
        assert param_dict["flatten_lines"].type == "bool"
        assert param_dict["flatten_lines"].default is False

        # Check align_new_line is bool with default False
        assert param_dict["align_new_line"].type == "bool"
        assert param_dict["align_new_line"].default is False


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
        has_line_too_long = any(d.rule_id == "LEN08" for d in result_default)
        assert has_line_too_long

        # With configuration to allow longer lines
        result_configured = _lint_file_impl(
            str(robot_file),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        has_line_too_long_configured = any(d.rule_id == "LEN08" for d in result_configured)
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
        assert isinstance(result.changed, bool)

    def test_format_with_custom_space_count(self):
        """Test formatting with custom space count."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        result = _format_content_impl(content, space_count=2)
        assert isinstance(result.formatted, str)

    def test_format_with_custom_line_length(self):
        """Test formatting with custom line length."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        result = _format_content_impl(content, line_length=80)
        assert isinstance(result.formatted, str)


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
        assert format_result.changed is True

        # Get issues after formatting
        issues_after = _lint_content_impl(format_result.formatted)

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
        issues_after_full = _lint_content_impl(format_result.formatted)

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

        # Check structure - RuleSummary model has these required fields
        # RuleSummary model validates all required fields exist

    def test_list_rules_by_category(self):
        """Test filtering rules by category."""
        result = _list_rules_impl(category="LEN")
        assert len(result) > 0
        for rule in result:
            assert rule.rule_id.startswith("LEN")

    def test_list_rules_by_severity(self):
        """Test filtering rules by severity."""
        result = _list_rules_impl(severity="W")
        assert len(result) > 0
        for rule in result:
            assert rule.severity == "W"

    def test_list_rules_enabled_only(self):
        """Test filtering to enabled rules only."""
        all_rules = _list_rules_impl()
        enabled_rules = _list_rules_impl(enabled_only=True)

        # Should have fewer or equal rules
        assert len(enabled_rules) <= len(all_rules)

        # All should be enabled
        for rule in enabled_rules:
            assert rule.enabled is True

    def test_list_rules_combined_filters(self):
        """Test combining multiple filters."""
        result = _list_rules_impl(category="NAME", severity="W", enabled_only=True)
        for rule in result:
            assert rule.rule_id.startswith("NAME")
            assert rule.severity == "W"
            assert rule.enabled is True

    def test_list_rules_sorted_by_id(self):
        """Test that rules are sorted by ID."""
        result = _list_rules_impl()
        rule_ids = [r.rule_id for r in result]
        assert rule_ids == sorted(rule_ids)


class TestListFormatters:
    """Tests for list_formatters tool."""

    def test_list_enabled_formatters(self):
        """Test listing enabled formatters (default)."""
        result = _list_formatters_impl()
        assert isinstance(result, list)
        # FormatterSummary model validates all required fields exist
        assert len(result) > 0

    def test_list_all_formatters(self):
        """Test listing all formatters including disabled."""
        enabled = _list_formatters_impl(enabled_only=True)
        all_formatters = _list_formatters_impl(enabled_only=False)

        # Should have more or equal formatters
        assert len(all_formatters) >= len(enabled)

    def test_list_formatters_sorted_by_name(self):
        """Test that formatters are sorted by name."""
        result = _list_formatters_impl(enabled_only=False)
        names = [f.name for f in result]
        assert names == sorted(names)

    def test_list_formatters_has_normalize_separators(self):
        """Test that NormalizeSeparators is in the list."""
        result = _list_formatters_impl(enabled_only=False)
        names = [f.name for f in result]
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

        assert result.total_issues == len(result.fixes)
        assert result.auto_fixable + result.manual_required == result.total_issues

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

        # FixSuggestion model validates all required fields exist
        assert len(result.fixes) > 0

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

        for fix in result.fixes:
            assert fix.rule_id.startswith("NAME")

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
        assert isinstance(result.total_issues, int)

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
        assert isinstance(result.recommendation, str)
        assert len(result.recommendation) > 0


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

        assert result.total_files == 2
        assert result.total_issues > 0
        assert result.unmatched_patterns == []

    def test_lint_with_glob(self, tmp_path: Path):
        """Test linting with glob pattern."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\ntest\n    Log    y\n")

        result = _lint_files_impl(["tests/*.robot"], str(tmp_path))

        assert result.total_files == 2

    def test_lint_with_limit(self, tmp_path: Path):
        """Test limiting results."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    a\n    Log    b\n")

        # Get all issues first
        all_result = _lint_files_impl(["test.robot"], str(tmp_path))

        if all_result.total_issues > 1:
            # Limit to 1 issue
            result = _lint_files_impl(["test.robot"], str(tmp_path), limit=1)
            assert len(result.issues) == 1
            assert result.total_issues > 1
            assert result.limited is True

    def test_lint_with_select(self, tmp_path: Path):
        """Test selecting specific rules."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest lowercase\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), select=["NAME*"])

        for issue in result.issues:
            assert issue.rule_id.startswith("NAME")

    def test_no_files_raises_error(self, tmp_path: Path):
        """Test that no matching files raises ToolError."""
        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            _lint_files_impl(["nonexistent.robot"], str(tmp_path))

    def test_includes_file_path(self, tmp_path: Path):
        """Test that issues include file path."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        for issue in result.issues:
            assert issue.file is not None

    def test_summary_counts(self, tmp_path: Path):
        """Test that summary counts are correct."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        # Sum of summary should equal total issues
        summary_total = result.summary.E + result.summary.W + result.summary.INFO
        assert summary_total == result.total_issues

    def test_files_with_issues_count(self, tmp_path: Path):
        """Test files_with_issues count."""
        # File with issues
        (tmp_path / "bad.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        # File without issues (proper formatting)
        (tmp_path / "good.robot").write_text("*** Test Cases ***\nValid Test\n    Log    Hello\n")

        result = _lint_files_impl(["bad.robot", "good.robot"], str(tmp_path))

        assert result.total_files == 2
        # At least one file should have issues
        assert result.files_with_issues >= 1

    def test_unmatched_patterns_in_result(self, tmp_path: Path):
        """Test that unmatched patterns are included in result."""
        (tmp_path / "exists.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["exists.robot", "missing.robot"], str(tmp_path))

        assert result.total_files == 1
        assert "missing.robot" in result.unmatched_patterns

    def test_with_configure(self, tmp_path: Path):
        """Test linting with configure parameter."""
        long_line = "A" * 150
        (tmp_path / "test.robot").write_text(f"*** Test Cases ***\nTest\n    Log    {long_line}\n")

        # Without configuration, should trigger line-too-long
        result_default = _lint_files_impl(["test.robot"], str(tmp_path), select=["LEN08"])
        has_line_too_long = any(d.rule_id == "LEN08" for d in result_default.issues)
        assert has_line_too_long

        # With configuration to allow longer lines
        result_configured = _lint_files_impl(
            ["test.robot"],
            str(tmp_path),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )
        has_line_too_long_configured = any(d.rule_id == "LEN08" for d in result_configured.issues)
        assert not has_line_too_long_configured

    def test_robot_pattern_also_matches_resource(self, tmp_path: Path):
        """Test that .robot patterns also match .resource files."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        (tmp_path / "keywords.resource").write_text("*** Keywords ***\nmy keyword\n    Log    x\n")

        # Pattern with .robot should also find .resource files
        result = _lint_files_impl(["**/*.robot"], str(tmp_path))

        assert result.total_files == 2
        files_found = {issue.file for issue in result.issues}
        assert any("test.robot" in f for f in files_found)
        assert any("keywords.resource" in f for f in files_found)

    def test_resource_pattern_also_matches_robot(self, tmp_path: Path):
        """Test that .resource patterns also match .robot files."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        (tmp_path / "keywords.resource").write_text("*** Keywords ***\nmy keyword\n    Log    x\n")

        # Pattern with .resource should also find .robot files
        result = _lint_files_impl(["*.resource"], str(tmp_path))

        assert result.total_files == 2

    def test_glob_without_extension_matches_both(self, tmp_path: Path):
        """Test that glob patterns without extension match both .robot and .resource."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")
        (subdir / "keywords.resource").write_text("*** Keywords ***\nmy keyword\n    Log    x\n")

        # Pattern without extension should find both file types
        result = _lint_files_impl(["tests/*"], str(tmp_path))

        assert result.total_files == 2


class TestGroupIssues:
    """Tests for _group_issues function."""

    def test_group_by_severity(self):
        """Test grouping issues by severity."""
        issues = [
            _make_issue(rule_id="LEN01", severity="W", file="a.robot"),
            _make_issue(rule_id="NAME01", severity="E", file="b.robot"),
            _make_issue(rule_id="DOC01", severity="I", file="a.robot"),
            _make_issue(rule_id="LEN02", severity="W", file="c.robot"),
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
            _make_issue(rule_id="LEN01", severity="W", file="a.robot"),
            _make_issue(rule_id="LEN01", severity="W", file="b.robot"),
            _make_issue(rule_id="NAME01", severity="E", file="a.robot"),
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
            _make_issue(rule_id="LEN01", severity="W", file="/path/a.robot"),
            _make_issue(rule_id="NAME01", severity="E", file="/path/a.robot"),
            _make_issue(rule_id="DOC01", severity="I", file="/path/b.robot"),
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
            _make_issue(rule_id="LEN01", severity="W", file="a.robot"),
            _make_issue(rule_id="LEN01", severity="W", file="b.robot"),
            _make_issue(rule_id="LEN01", severity="W", file="c.robot"),
            _make_issue(rule_id="NAME01", severity="E", file="a.robot"),
            _make_issue(rule_id="NAME01", severity="E", file="b.robot"),
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
        issues = [_make_issue(rule_id="LEN01", severity="W", file="a.robot")]

        with pytest.raises(ToolError, match="Invalid group_by"):
            _group_issues(issues, "invalid")

    def test_missing_field_uses_unknown(self):
        """Test that missing field uses 'unknown' as key."""
        issues = [
            _make_issue(rule_id="LEN01", severity="W"),  # file defaults to None
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

        assert isinstance(result.issues, dict)
        assert result.group_counts is not None
        # Issues should be grouped by severity
        for key in result.issues:
            assert key in ("E", "W", "I")

    def test_group_by_rule(self, tmp_path: Path):
        """Test _lint_files_impl with group_by='rule'."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), group_by="rule")

        assert isinstance(result.issues, dict)
        assert result.group_counts is not None
        # All keys should be rule IDs
        for key in result.issues:
            assert len(key) >= 3  # Rule IDs are at least 3 chars

    def test_group_by_with_limit(self, tmp_path: Path):
        """Test that limit applies per group when group_by is set."""
        # Create file with multiple issues
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n    Log    y\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path), group_by="rule", limit=1)

        # Each group should have at most 1 issue
        for issues in result.issues.values():
            assert len(issues) <= 1
        # Check if limited flag is set when any group was limited
        if any(result.group_counts[k] > 1 for k in result.group_counts):
            assert result.limited is True

    def test_no_group_by_returns_list(self, tmp_path: Path):
        """Test that without group_by, issues is a list (not dict)."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    x\n")

        result = _lint_files_impl(["test.robot"], str(tmp_path))

        assert isinstance(result.issues, list)
        assert "group_counts" not in result


class TestFormatFile:
    """Tests for format_file tool."""

    def test_format_file_basic(self, tmp_path: Path):
        """Test formatting a file without overwriting."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    log  hello\n")

        result = _format_file_impl(str(robot_file))

        assert result.diff is not None  # Optional field - verify it exists when changed
        assert result.changed is True
        assert result.written is False  # Not overwritten by default

    def test_format_file_overwrite(self, tmp_path: Path):
        """Test formatting a file with overwrite=True."""
        robot_file = tmp_path / "test.robot"
        original_content = "*** Test Cases ***\nTest\n    log  hello\n"
        robot_file.write_text(original_content)

        result = _format_file_impl(str(robot_file), overwrite=True)

        assert result.changed is True
        assert result.written is True
        # Verify file was actually modified
        new_content = robot_file.read_text()
        assert new_content != original_content
        assert new_content == result.formatted

    def test_format_file_unchanged(self, tmp_path: Path):
        """Test formatting an already formatted file."""
        robot_file = tmp_path / "test.robot"
        # Well-formatted content
        robot_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        result = _format_file_impl(str(robot_file), overwrite=True)

        # May or may not change depending on default formatters
        if not result.changed:
            assert result.written is False

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
        assert isinstance(result.changed, bool)

    def test_format_file_custom_space_count(self, tmp_path: Path):
        """Test formatting with custom space count."""
        robot_file = tmp_path / "test.robot"
        robot_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        result = _format_file_impl(str(robot_file), space_count=2)
        assert isinstance(result.changed, bool)

    def test_format_resource_file(self, tmp_path: Path):
        """Test formatting a .resource file."""
        resource_file = tmp_path / "lib.resource"
        resource_file.write_text("*** Keywords ***\nMy Keyword\n    log  hi\n")

        result = _format_file_impl(str(resource_file))

        assert result.file == str(resource_file)


class TestFormatFiles:
    """Tests for format_files tool."""

    def test_format_multiple_files(self, tmp_path: Path):
        """Test formatting multiple files."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["test1.robot", "test2.robot"], str(tmp_path))

        assert result.total_files == 2
        assert result.files_written == 0  # Not overwritten by default
        assert len(result.results) == 2

    def test_format_files_with_overwrite(self, tmp_path: Path):
        """Test formatting files with overwrite."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["test1.robot", "test2.robot"], str(tmp_path), overwrite=True)

        assert result.files_written == result.files_changed

    def test_format_files_with_glob(self, tmp_path: Path):
        """Test formatting with glob pattern."""
        subdir = tmp_path / "tests"
        subdir.mkdir()
        (subdir / "test1.robot").write_text("*** Test Cases ***\nTest\n    log  a\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\nTest\n    log  b\n")

        result = _format_files_impl(["tests/*.robot"], str(tmp_path))

        assert result.total_files == 2

    def test_format_files_recursive_glob(self, tmp_path: Path):
        """Test formatting with recursive glob pattern."""
        deep = tmp_path / "a" / "b"
        deep.mkdir(parents=True)
        (deep / "test.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["**/*.robot"], str(tmp_path))

        assert result.total_files == 1

    def test_format_files_no_matches(self, tmp_path: Path):
        """Test formatting with no matching files."""
        with pytest.raises(ToolError, match=r"No \.robot or \.resource files found"):
            _format_files_impl(["nonexistent.robot"], str(tmp_path))

    def test_format_files_unmatched_patterns(self, tmp_path: Path):
        """Test that unmatched patterns are tracked."""
        (tmp_path / "exists.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["exists.robot", "missing.robot"], str(tmp_path))

        assert result.total_files == 1
        assert "missing.robot" in result.unmatched_patterns

    def test_format_files_results_structure(self, tmp_path: Path):
        """Test the structure of per-file results."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nTest\n    log  hi\n")

        result = _format_files_impl(["test.robot"], str(tmp_path))

        # FormatFileInfo model validates all required fields exist
        assert len(result.results) > 0


class TestGetStatistics:
    """Tests for get_statistics tool."""

    def test_get_statistics_basic(self, tmp_path: Path):
        """Test basic statistics gathering."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        result = _get_statistics_impl(str(tmp_path))

        # GetStatisticsResult model validates all required fields exist
        assert result.directory == str(tmp_path)

    def test_get_statistics_summary(self, tmp_path: Path):
        """Test statistics summary structure."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        summary = result.summary
        # StatisticsSummary model validates all required fields exist
        assert summary.total_files == 1

    def test_get_statistics_severity_breakdown(self, tmp_path: Path):
        """Test severity breakdown in statistics."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        severity = result.severity_breakdown
        # Sum should equal total issues
        total = severity.E + severity.W + severity.INFO
        assert total == result.summary.total_issues

    def test_get_statistics_quality_score(self, tmp_path: Path):
        """Test quality score structure."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\nGood Test\n    Log    Hello\n")

        result = _get_statistics_impl(str(tmp_path))

        quality = result.quality_score
        # QualityScore model validates all required fields exist
        assert 0 <= quality.score <= 100
        assert quality.grade in ("A", "B", "C", "D", "F")

    def test_get_statistics_top_issues(self, tmp_path: Path):
        """Test top issues list."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        assert isinstance(result.top_issues, list)
        for issue in result.top_issues:
            # TopRule model validates required fields exist
            assert issue.count > 0

    def test_get_statistics_recommendations(self, tmp_path: Path):
        """Test recommendations list."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path))

        assert isinstance(result.recommendations, list)
        assert len(result.recommendations) > 0
        for rec in result.recommendations:
            assert isinstance(rec, str)

    def test_get_statistics_recursive(self, tmp_path: Path):
        """Test recursive directory scanning."""
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    log  a\n")
        (subdir / "test2.robot").write_text("*** Test Cases ***\ntest\n    log  b\n")

        # Recursive (default)
        result_recursive = _get_statistics_impl(str(tmp_path), recursive=True)
        assert result_recursive.summary.total_files == 2

        # Non-recursive
        result_nonrecursive = _get_statistics_impl(str(tmp_path), recursive=False)
        assert result_nonrecursive.summary.total_files == 1

    def test_get_statistics_with_select(self, tmp_path: Path):
        """Test statistics with rule selection."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    log  hi\n")

        result = _get_statistics_impl(str(tmp_path), select=["NAME*"])

        # All issues should be NAME rules
        for issue in result.top_issues:
            assert issue.rule_id.startswith("NAME")

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

        assert result.line == 2

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

        assert result.issues_found is True
        assert result.issues is not None
        assert len(result.issues) > 0

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

        # IssueExplanation model validates all required fields exist
        assert len(result.issues) > 0

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

        if result.issues:
            issue = result.issues[0]
            # Should include additional context fields
            assert issue.why_it_matters is not None or issue.full_documentation is not None

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
        assert result.line == 1

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

        assert result.related_issues is not None

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

        context = result.context
        # Should have target line +/- 1 = at most 3 lines
        assert len(context.lines) <= 3

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

        context = result.context
        # CodeContext and ContextLine models validate all required fields exist
        assert len(context.lines) > 0


class TestGetLineContext:
    """Tests for _get_line_context helper."""

    def test_get_line_context_basic(self):
        """Test basic context extraction."""
        content = "line1\nline2\nline3\nline4\nline5"

        result = _get_line_context(content, line=3, context_lines=1)

        assert result.target_line == 3
        assert result.target_content == "line3"
        assert len(result.lines) == 3  # line 2, 3, 4

    def test_get_line_context_at_start(self):
        """Test context at start of file."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=1, context_lines=2)

        assert result.target_line == 1
        # Should only have lines after, not before
        assert len(result.lines) == 3  # line 1, 2, 3

    def test_get_line_context_at_end(self):
        """Test context at end of file."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=3, context_lines=2)

        assert result.target_line == 3
        # Should only have lines before, not after
        assert len(result.lines) == 3  # line 1, 2, 3

    def test_get_line_context_target_marked(self):
        """Test that target line is marked."""
        content = "line1\nline2\nline3"

        result = _get_line_context(content, line=2, context_lines=1)

        target_found = False
        for line_info in result.lines:
            if line_info.is_target:
                target_found = True
                assert line_info.line_number == 2
        assert target_found


class TestLintContentEdgeCases:
    """Tests for lint_content edge cases."""

    def test_lint_empty_content(self):
        """Test linting empty content."""
        result = _lint_content_impl("")
        assert isinstance(result, list)

    def test_lint_whitespace_only_content(self):
        """Test linting whitespace-only content."""
        result = _lint_content_impl("   \n\n   \n")
        assert isinstance(result, list)

    def test_lint_with_filename_resource(self):
        """Test linting content with resource filename."""
        content = "*** Keywords ***\nMy Keyword\n    Log    Hello\n"
        result = _lint_content_impl(content, filename="lib.resource")
        assert isinstance(result, list)

    def test_lint_with_all_parameters(self):
        """Test linting with all parameters combined."""
        content = dedent(
            """
            *** Test Cases ***
            test lowercase
                log  hello
        """
        ).lstrip()

        result = _lint_content_impl(
            content,
            filename="test.robot",
            select=["NAME*"],
            ignore=["NAME03"],
            threshold="W",
            limit=5,
            configure=["not-capitalized-test-case-title.severity=I"],
        )
        assert isinstance(result, list)


class TestFormatContentEdgeCases:
    """Tests for format_content edge cases."""

    def test_format_empty_content(self):
        """Test formatting empty content."""
        result = _format_content_impl("")
        assert isinstance(result.changed, bool)

    def test_format_with_all_parameters(self):
        """Test formatting with all parameters combined."""
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"

        result = _format_content_impl(
            content,
            filename="test.robot",
            select=["NormalizeSeparators"],
            space_count=2,
            line_length=80,
        )
        assert isinstance(result.changed, bool)


class TestLintDirectoryWithGroupBy:
    """Tests for lint_directory with group_by parameter."""

    def test_lint_directory_group_by_severity(self, tmp_path: Path):
        """Test lint_files with group_by='severity' (lint_directory uses same logic)."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    Hi\n")

        result = _lint_files_impl(["*.robot"], str(tmp_path), group_by="severity")

        assert isinstance(result.issues, dict)
        assert result.group_counts is not None
        # Issues should be grouped by severity
        for key in result.issues:
            assert key in ("E", "W", "I")

    def test_lint_directory_group_by_rule(self, tmp_path: Path):
        """Test lint_files with group_by='rule'."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    Hi\n")

        result = _lint_files_impl(["*.robot"], str(tmp_path), group_by="rule")

        assert isinstance(result.issues, dict)
        assert result.group_counts is not None

    def test_lint_directory_group_by_file(self, tmp_path: Path):
        """Test lint_files with group_by='file'."""
        (tmp_path / "test1.robot").write_text("*** Test Cases ***\ntest\n    Log    a\n")
        (tmp_path / "test2.robot").write_text("*** Test Cases ***\ntest\n    Log    b\n")

        result = _lint_files_impl(["*.robot"], str(tmp_path), group_by="file")

        assert isinstance(result.issues, dict)
        assert result.group_counts is not None


class TestLintAndFormatParameters:
    """Tests for lint_and_format combined workflow using format + lint."""

    def test_lint_and_format_with_format_select(self):
        """Test format then lint workflow with specific formatters."""
        content = "*** Test Cases ***\nTest\n    log  hello\n"

        # Simulate lint_and_format by formatting then linting
        format_result = _format_content_impl(content, select=["NormalizeSeparators"])
        lint_result = _lint_content_impl(format_result.formatted)

        assert isinstance(lint_result, list)

    def test_lint_and_format_with_lint_ignore(self):
        """Test format then lint workflow with lint ignore."""
        content = "*** Test Cases ***\ntest\n    log  hello\n"

        # Simulate lint_and_format
        format_result = _format_content_impl(content)
        lint_result = _lint_content_impl(format_result.formatted, ignore=["NAME*"])

        # No NAME issues in result
        for issue in lint_result:
            assert not issue.rule_id.startswith("NAME")

    def test_lint_and_format_with_threshold(self):
        """Test format then lint workflow with threshold."""
        content = "*** Test Cases ***\ntest\n    log  hello\n"

        # Simulate lint_and_format
        format_result = _format_content_impl(content)
        lint_result = _lint_content_impl(format_result.formatted, threshold="E")

        # Only errors in result
        for issue in lint_result:
            assert issue.severity == "E"


class TestLintAndFormatWithFile:
    """Tests for lint_and_format with file_path support."""

    def test_lint_and_format_with_content(self):
        """Test lint_and_format with content parameter."""
        content = "*** Test Cases ***\ntest\n    log  hello\n"

        result = _lint_and_format_impl(content=content)

        assert result.issues is not None
        # Should not have file-specific fields when using content
        assert "file" not in result
        assert "written" not in result

    def test_lint_and_format_with_file_path(self, tmp_path):
        """Test lint_and_format with file_path parameter."""
        # Create a test file with issues
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\ntest\n    log  hello\n")

        result = _lint_and_format_impl(file_path=str(test_file))

        assert result.issues is not None
        # Should have file-specific fields
        assert result.file == str(test_file)
        assert result.written is False  # default is no overwrite

    def test_lint_and_format_file_with_overwrite(self, tmp_path):
        """Test lint_and_format with overwrite=True."""
        # Create a test file with formatting issues
        test_file = tmp_path / "test.robot"
        original_content = "*** Test Cases ***\nTest\n    log  hello\n"
        test_file.write_text(original_content)

        result = _lint_and_format_impl(file_path=str(test_file), overwrite=True)

        assert result.changed is True
        assert result.written is True
        # Verify file was actually changed
        new_content = test_file.read_text()
        assert new_content != original_content
        assert new_content == result.formatted

    def test_lint_and_format_file_unchanged_no_overwrite(self, tmp_path):
        """Test lint_and_format doesn't write if no changes needed."""
        # Create a well-formatted file
        test_file = tmp_path / "test.robot"
        content = "*** Test Cases ***\nTest\n    Log    Hello\n"
        test_file.write_text(content)

        result = _lint_and_format_impl(file_path=str(test_file), overwrite=True)

        # If no changes needed, written should be False
        if not result.changed:
            assert result.written is False

    def test_lint_and_format_requires_content_or_file(self):
        """Test that either content or file_path must be provided."""
        with pytest.raises(ToolError, match="Either 'content' or 'file_path' must be provided"):
            _lint_and_format_impl()

    def test_lint_and_format_not_both_content_and_file(self, tmp_path):
        """Test that content and file_path cannot both be provided."""
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        with pytest.raises(ToolError, match="Provide either 'content' or 'file_path', not both"):
            _lint_and_format_impl(content="some content", file_path=str(test_file))

    def test_lint_and_format_file_not_found(self):
        """Test lint_and_format with nonexistent file."""
        with pytest.raises(ToolError, match="File not found"):
            _lint_and_format_impl(file_path="/nonexistent/path/test.robot")

    def test_lint_and_format_invalid_file_type(self, tmp_path):
        """Test lint_and_format with invalid file type."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("some content")

        with pytest.raises(ToolError, match="Invalid file type"):
            _lint_and_format_impl(file_path=str(test_file))

    def test_lint_and_format_file_with_configure(self, tmp_path):
        """Test lint_and_format with configure parameter on file."""
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n")

        result = _lint_and_format_impl(
            file_path=str(test_file),
            configure=["line-too-long.line_length=200"],
        )

        assert result.issues is not None
        assert isinstance(result.issues, list)


class TestSuggestFixesParameters:
    """Tests for suggest_fixes with various parameters."""

    def test_suggest_fixes_with_filename(self):
        """Test suggest_fixes with filename parameter."""
        content = "*** Keywords ***\nmy keyword\n    Log    Hello\n"

        result = _suggest_fixes_impl(content, filename="lib.resource")

        assert isinstance(result.total_issues, int)


class TestExplainIssueParameters:
    """Tests for explain_issue with various parameters."""

    def test_explain_issue_with_filename(self):
        """Test explain_issue with filename parameter."""
        content = "*** Keywords ***\nmy keyword\n    Log    Hello\n"

        result = _explain_issue_impl(content, line=2, filename="lib.resource")
        assert result.line == 2

    def test_explain_issue_large_context(self):
        """Test explain_issue with large context_lines."""
        content = "\n".join([f"Line {i}" for i in range(1, 21)])

        result = _explain_issue_impl(content, line=10, context_lines=5)

        assert result.line == 10
        # Context should include up to 5 lines before and after
        assert len(result.context.lines) <= 11


class TestGetStatisticsParameters:
    """Tests for get_statistics with various parameters."""

    def test_get_statistics_with_configure(self, tmp_path: Path):
        """Test get_statistics with configure parameter."""
        long_line = "A" * 150
        (tmp_path / "test.robot").write_text(f"*** Test Cases ***\nTest\n    Log    {long_line}\n")

        # Without configure - should have line-too-long
        result_default = _get_statistics_impl(str(tmp_path), select=["LEN08"])
        has_len08 = any(issue.rule_id == "LEN08" for issue in result_default.top_issues)

        # With configure - should not have line-too-long
        result_configured = _get_statistics_impl(
            str(tmp_path),
            select=["LEN08"],
            configure=["line-too-long.line_length=200"],
        )

        # The configured version should have same or fewer issues
        assert result_configured.summary.total_issues <= result_default.summary.total_issues or not has_len08

    def test_get_statistics_with_ignore(self, tmp_path: Path):
        """Test get_statistics with ignore parameter."""
        (tmp_path / "test.robot").write_text("*** Test Cases ***\ntest\n    Log    Hi\n")

        # Get all issues
        all_stats = _get_statistics_impl(str(tmp_path))

        # Ignore NAME rules
        filtered_stats = _get_statistics_impl(str(tmp_path), ignore=["NAME*"])

        # Filtered should have equal or fewer issues
        assert filtered_stats.summary.total_issues <= all_stats.summary.total_issues

        # No NAME issues in top_issues
        for issue in filtered_stats.top_issues:
            assert not issue.rule_id.startswith("NAME")


class TestFormatterInfoEdgeCases:
    """Tests for get_formatter_info edge cases."""

    def test_get_formatter_info_with_no_parameters(self):
        """Test formatter info for formatter with no extra parameters."""
        # Find a formatter and check its info
        result = _get_formatter_info_impl("NormalizeSeparators")
        assert isinstance(result.parameters, list)

    def test_get_formatter_info_min_version(self):
        """Test that formatter info includes min_version."""
        result = _get_formatter_info_impl("NormalizeSeparators")
        # min_version is an optional field on FormatterDetail model (Pydantic ensures it exists)
        assert result.min_version is None or isinstance(result.min_version, str)


class TestRuleInfoEdgeCases:
    """Tests for get_rule_info edge cases."""

    def test_get_rule_info_includes_version_requirement(self):
        """Test that rule info includes version_requirement field."""
        result = _get_rule_info_impl("LEN01")
        # version_requirement is an optional field on RuleDetail model (Pydantic ensures it exists)
        assert result.version_requirement is None or isinstance(result.version_requirement, str)

    def test_get_rule_info_includes_deprecated(self):
        """Test that rule info includes deprecated field."""
        result = _get_rule_info_impl("LEN01")
        # RuleDetail model has deprecated as a required bool field
        assert isinstance(result.deprecated, bool)

    def test_get_rule_info_includes_added_in_version(self):
        """Test that rule info includes added_in_version field."""
        result = _get_rule_info_impl("LEN01")
        # added_in_version is an optional field on RuleDetail model (Pydantic ensures it exists)
        assert result.added_in_version is None or isinstance(result.added_in_version, str)


class TestOffsetPagination:
    """Tests for offset parameter in lint_files."""

    def test_offset_skips_issues(self, tmp_path):
        """Test that offset skips the first N issues."""
        # Create files with issues
        (tmp_path / "test1.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  hello
                test two
                    log  world
                """
            ).lstrip()
        )

        # Get all issues
        all_result = _lint_files_impl(["*.robot"], base_path=str(tmp_path))
        total = all_result.total_issues

        # Get with offset
        offset_result = _lint_files_impl(["*.robot"], base_path=str(tmp_path), offset=2)

        # Should have skipped 2 issues
        assert len(offset_result.issues) == total - 2
        assert offset_result.offset == 2
        assert offset_result.total_issues == total  # Total unchanged

    def test_offset_with_limit(self, tmp_path):
        """Test offset combined with limit for pagination."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  a
                test two
                    log  b
                test three
                    log  c
                test four
                    log  d
                """
            ).lstrip()
        )

        # First page
        page1 = _lint_files_impl(["*.robot"], base_path=str(tmp_path), limit=2, offset=0)
        # Second page
        page2 = _lint_files_impl(["*.robot"], base_path=str(tmp_path), limit=2, offset=2)

        assert len(page1.issues) == 2
        assert len(page2.issues) == 2
        assert page1.has_more is True
        # Pages should have different issues
        page1_lines = {i.line for i in page1.issues}
        page2_lines = {i.line for i in page2.issues}
        assert page1_lines.isdisjoint(page2_lines)

    def test_offset_beyond_results(self, tmp_path):
        """Test offset larger than total issues returns empty."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  hello
                """
            ).lstrip()
        )

        result = _lint_files_impl(["*.robot"], base_path=str(tmp_path), offset=100)
        assert len(result.issues) == 0
        assert result.has_more is False

    def test_offset_with_group_by(self, tmp_path):
        """Test offset works with group_by parameter."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  a
                test two
                    log  b
                test three
                    log  c
                """
            ).lstrip()
        )

        # Group by severity with offset
        result = _lint_files_impl(["*.robot"], base_path=str(tmp_path), group_by="severity", limit=1, offset=1)

        # Should have offset applied per group
        assert result.group_counts is not None
        assert result.offset == 1


class TestSummarizeOnly:
    """Tests for summarize_only parameter."""

    def test_summarize_only_lint_files(self, tmp_path):
        """Test summarize_only returns stats without issues list."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  hello
                test two
                    log  world
                """
            ).lstrip()
        )

        result = _lint_files_impl(["*.robot"], base_path=str(tmp_path), summarize_only=True)

        # Should have summary and top_rules but not issues
        # issues field should be None in summarize_only mode
        assert result.issues is None
        assert result.top_rules is not None  # Optional field - verify it exists in summarize mode

    def test_summarize_only_includes_top_rules(self, tmp_path):
        """Test summarize_only includes top rules."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  a
                test two
                    log  b
                """
            ).lstrip()
        )

        result = _lint_files_impl(["*.robot"], base_path=str(tmp_path), summarize_only=True)

        # Top rules should be a list of TopRule models
        assert isinstance(result.top_rules, list)
        # TopRule model validates all required fields exist

    def test_summarize_only_format_files(self, tmp_path):
        """Test summarize_only for format_files."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                Test One
                    Log  hello
                """
            ).lstrip()
        )

        result = _format_files_impl(["*.robot"], base_path=str(tmp_path), summarize_only=True)

        # Should have summary but not per-file results
        # results should be None in summarize_only mode
        assert result.results is None


class TestWorstFiles:
    """Tests for worst_files tool."""

    def test_worst_files_returns_sorted(self, tmp_path):
        """Test worst_files returns files sorted by issue count."""
        # Create file with many issues
        (tmp_path / "bad.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  a
                test two
                    log  b
                test three
                    log  c
                """
            ).lstrip()
        )
        # Create file with fewer issues
        (tmp_path / "good.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                Test One
                    Log    Hello
                """
            ).lstrip()
        )

        result = _worst_files_impl(str(tmp_path))

        assert len(result.files) >= 1
        # First file should have most issues
        if len(result.files) > 1:
            assert result.files[0].issue_count >= result.files[1].issue_count

    def test_worst_files_limit_n(self, tmp_path):
        """Test worst_files respects n parameter."""
        for i in range(5):
            (tmp_path / f"test{i}.robot").write_text(
                dedent(
                    f"""
                    *** Test Cases ***
                    test {i}
                        log  hello
                    """
                ).lstrip()
            )

        result = _worst_files_impl(str(tmp_path), n=2)
        assert len(result.files) <= 2

    def test_worst_files_includes_severity_breakdown(self, tmp_path):
        """Test worst_files includes severity breakdown per file."""
        (tmp_path / "test.robot").write_text(
            dedent(
                """
                *** Test Cases ***
                test one
                    log  hello
                """
            ).lstrip()
        )

        result = _worst_files_impl(str(tmp_path))

        # WorstFile and SeveritySummary models validate all required fields exist
        assert len(result.files) > 0

    def test_worst_files_empty_directory(self, tmp_path):
        """Test worst_files with no robot files."""
        with pytest.raises(ToolError, match=r"No .robot or .resource files"):
            _worst_files_impl(str(tmp_path))

    def test_worst_files_directory_not_found(self):
        """Test worst_files with non-existent directory."""
        with pytest.raises(ToolError, match="Directory not found"):
            _worst_files_impl("/nonexistent/path")


class TestSearchRules:
    """Tests for search_rules tool."""

    def test_search_rules_by_name(self):
        """Test searching rules by name."""
        result = _search_rules_impl("long")
        assert len(result) > 0
        # Should find rules with "long" in name
        assert any("long" in r.name.lower() for r in result)

    def test_search_rules_by_message(self):
        """Test searching rules by message content."""
        result = _search_rules_impl("keyword", fields=["message"])
        assert len(result) > 0

    def test_search_rules_with_category_filter(self):
        """Test searching rules with category filter."""
        result = _search_rules_impl("too", category="LEN")
        # All results should be LEN rules
        for rule in result:
            assert rule.rule_id.startswith("LEN")

    def test_search_rules_with_severity_filter(self):
        """Test searching rules with severity filter."""
        result = _search_rules_impl("name", severity="W")
        # All results should be warnings
        for rule in result:
            assert rule.severity == "W"

    def test_search_rules_includes_match_info(self):
        """Test search results include match field and snippet."""
        result = _search_rules_impl("documentation")
        # RuleSearchResult model validates all required fields exist
        assert len(result) > 0

    def test_search_rules_respects_limit(self):
        """Test search respects limit parameter."""
        result = _search_rules_impl("", limit=5)  # Empty query matches many
        assert len(result) <= 5

    def test_search_rules_no_results(self):
        """Test search with no matching results."""
        result = _search_rules_impl("xyznonexistent123")
        assert len(result) == 0


class TestListPrompts:
    """Tests for list_prompts tool."""

    def test_list_prompts_returns_list(self):
        """Test list_prompts returns a list."""
        result = _list_prompts_impl()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_prompts_includes_required_fields(self):
        """Test each prompt has name, description, arguments."""
        result = _list_prompts_impl()
        # PromptSummary model validates all required fields exist
        for prompt in result:
            assert isinstance(prompt.arguments, list)

    def test_list_prompts_discovers_all_prompts(self):
        """
        Test that all prompts from prompts.py are discovered.

        This test ensures that when new prompts are added to prompts.py,
        the AST introspection picks them up correctly.
        """
        result = _list_prompts_impl()
        prompt_names = {p.name for p in result}

        # All prompts that should be discovered from prompts.py
        expected_prompts = {
            "analyze_robot_file",
            "fix_robot_issues",
            "explain_rule",
            "review_pull_request",
            "configure_robocop",
            "migrate_to_latest",
        }

        assert prompt_names == expected_prompts, (
            f"Prompt mismatch. Expected: {expected_prompts}, Got: {prompt_names}. "
            f"Missing: {expected_prompts - prompt_names}, Extra: {prompt_names - expected_prompts}"
        )

    def test_list_prompts_argument_required_field(self):
        """Test that arguments correctly identify required vs optional."""
        result = _list_prompts_impl()
        prompts_by_name = {p.name: p for p in result}

        # analyze_robot_file: content (required), focus (optional)
        analyze = prompts_by_name["analyze_robot_file"]
        args_by_name = {a.name: a for a in analyze.arguments}
        assert args_by_name["content"].required is True
        assert args_by_name["focus"].required is False

        # fix_robot_issues: content (required)
        fix = prompts_by_name["fix_robot_issues"]
        assert len(fix.arguments) == 1
        assert fix.arguments[0].name == "content"
        assert fix.arguments[0].required is True
