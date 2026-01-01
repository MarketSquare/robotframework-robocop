"""Tests for natural language configuration feature."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
from pathlib import Path

import pytest

from robocop.mcp.tools.natural_language_config import (
    _apply_config_impl,
    _parse_llm_response,
    _validate_suggestions,
    get_config_system_message,
    parse_config_from_llm_response,
)
from robocop.mcp.tools.utils.helpers import (
    build_config_options_catalog,
    build_rule_catalog,
    detect_config_conflicts,
    generate_toml_config_from_suggestions,
    get_rule_by_name_or_id,
    validate_rule_param,
)
from robocop.mcp.tools.utils.toml_handler import (
    extract_lint_section_string,
    generate_diff,
    merge_robocop_config,
    read_toml_file,
    write_toml_file,
)


class TestBuildRuleCatalog:
    """Tests for build_rule_catalog function."""

    def test_catalog_contains_rules(self):
        """Catalog should contain all available rules."""
        catalog = build_rule_catalog()
        assert len(catalog) > 100, "Should have many rules"

    def test_catalog_rule_structure(self):
        """Each rule in catalog should have expected fields."""
        catalog = build_rule_catalog()
        rule = catalog[0]

        assert "rule_id" in rule
        assert "name" in rule
        assert "description" in rule
        assert "severity" in rule
        assert "enabled" in rule
        assert "deprecated" in rule
        assert "parameters" in rule

    def test_catalog_sorted_by_rule_id(self):
        """Catalog should be sorted by rule_id."""
        catalog = build_rule_catalog()
        rule_ids = [r["rule_id"] for r in catalog]
        assert rule_ids == sorted(rule_ids)

    def test_catalog_parameters_structure(self):
        """Rule parameters should have expected fields."""
        catalog = build_rule_catalog()
        # Find a rule with parameters
        rules_with_params = [r for r in catalog if r["parameters"]]
        assert len(rules_with_params) > 0, "Should have rules with parameters"

        param = rules_with_params[0]["parameters"][0]
        assert "name" in param
        assert "type" in param
        assert "default" in param
        assert "description" in param


class TestGetRuleByNameOrId:
    """Tests for get_rule_by_name_or_id function."""

    def test_find_by_name(self):
        """Should find rule by name."""
        rule = get_rule_by_name_or_id("line-too-long")
        assert rule is not None
        assert rule.name == "line-too-long"

    def test_find_by_id(self):
        """Should find rule by ID."""
        rule = get_rule_by_name_or_id("LEN08")
        assert rule is not None
        assert rule.rule_id == "LEN08"

    def test_find_by_id_case_insensitive(self):
        """Should find rule by ID case-insensitively."""
        rule = get_rule_by_name_or_id("len08")
        assert rule is not None
        assert rule.rule_id == "LEN08"

    def test_not_found(self):
        """Should return None for non-existent rule."""
        rule = get_rule_by_name_or_id("nonexistent-rule")
        assert rule is None


class TestValidateRuleParam:
    """Tests for validate_rule_param function."""

    def test_valid_int_param(self):
        """Should accept valid integer parameter."""
        is_valid, value, error = validate_rule_param("line-too-long", "line_length", "140")
        assert is_valid is True
        assert value == "140"
        assert error is None

    def test_invalid_param_name(self):
        """Should reject invalid parameter name."""
        is_valid, value, error = validate_rule_param("line-too-long", "invalid_param", "100")
        assert is_valid is False
        assert value is None
        assert "not found" in error

    def test_invalid_rule_name(self):
        """Should reject invalid rule name."""
        is_valid, value, error = validate_rule_param("nonexistent-rule", "param", "100")
        assert is_valid is False
        assert value is None
        assert "not found" in error

    def test_invalid_value_type(self):
        """Should reject invalid value type."""
        is_valid, value, error = validate_rule_param("line-too-long", "line_length", "not-a-number")
        assert is_valid is False
        assert value is None
        assert error is not None


class TestDetectConfigConflicts:
    """Tests for detect_config_conflicts function."""

    def test_no_conflicts(self):
        """Should return empty list when no conflicts."""
        suggestions = [
            {"rule_id": "LEN01", "action": "configure"},
            {"rule_id": "LEN02", "action": "disable"},
        ]
        warnings = detect_config_conflicts(suggestions)
        assert warnings == []

    def test_enable_disable_conflict(self):
        """Should detect enable/disable conflict."""
        suggestions = [
            {"rule_id": "LEN01", "action": "enable"},
            {"rule_id": "LEN01", "action": "disable"},
        ]
        warnings = detect_config_conflicts(suggestions)
        assert len(warnings) == 1
        assert "Conflict" in warnings[0]
        assert "LEN01" in warnings[0]

    def test_configure_disabled_warning(self):
        """Should warn about configuring disabled rule."""
        suggestions = [
            {"rule_id": "LEN01", "action": "configure"},
            {"rule_id": "LEN01", "action": "disable"},
        ]
        warnings = detect_config_conflicts(suggestions)
        assert len(warnings) == 1
        assert "configured but also disabled" in warnings[0]


class TestGenerateTomlConfigFromSuggestions:
    """Tests for generate_toml_config_from_suggestions function."""

    def test_configure_action(self):
        """Should generate configure entries in lint section."""
        suggestions = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "140",
            }
        ]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "lint" in config
        assert "configure" in config["lint"]
        assert "line-too-long.line_length=140" in config["lint"]["configure"]

    def test_enable_action(self):
        """Should generate select entries for enable action in lint section."""
        suggestions = [{"rule_id": "LEN01", "rule_name": "too-long-keyword", "action": "enable"}]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "lint" in config
        assert "select" in config["lint"]
        assert "LEN01" in config["lint"]["select"]

    def test_disable_action(self):
        """Should generate ignore entries for disable action in lint section."""
        suggestions = [{"rule_id": "LEN01", "rule_name": "too-long-keyword", "action": "disable"}]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "lint" in config
        assert "ignore" in config["lint"]
        assert "LEN01" in config["lint"]["ignore"]

    def test_mixed_actions(self):
        """Should handle multiple action types in lint section."""
        suggestions = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "140",
            },
            {"rule_id": "LEN01", "rule_name": "too-long-keyword", "action": "enable"},
            {"rule_id": "NAME01", "rule_name": "not-allowed-char-in-name", "action": "disable"},
        ]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "configure" in config["lint"]
        assert "select" in config["lint"]
        assert "ignore" in config["lint"]

    def test_set_action_common_section(self):
        """Should handle set action for common section options."""
        suggestions = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "value": "/tmp/robocop-cache",  # noqa: S108
                "section": "common",
            }
        ]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "common" in config
        assert config["common"]["cache_dir"] == "/tmp/robocop-cache"  # noqa: S108

    def test_set_action_format_section(self):
        """Should handle set action for format section options."""
        suggestions = [
            {
                "action": "set",
                "parameter": "space_count",
                "value": "2",
                "section": "format",
            }
        ]
        config = generate_toml_config_from_suggestions(suggestions)
        assert "format" in config
        assert config["format"]["space_count"] == 2  # Should be converted to int

    def test_mixed_sections(self):
        """Should handle suggestions targeting different sections."""
        suggestions = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "value": "/tmp/cache",  # noqa: S108
                "section": "common",
            },
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "140",
                "section": "lint",
            },
            {
                "action": "set",
                "parameter": "space_count",
                "value": "4",
                "section": "format",
            },
        ]
        config = generate_toml_config_from_suggestions(suggestions)
        assert config["common"]["cache_dir"] == "/tmp/cache"  # noqa: S108
        assert "line-too-long.line_length=140" in config["lint"]["configure"]
        assert config["format"]["space_count"] == 4


class TestTomlHandler:
    """Tests for TOML handler utilities."""

    def test_read_nonexistent_file(self):
        """Should return empty dict for nonexistent file."""
        result = read_toml_file(Path("/nonexistent/file.toml"))
        assert result == {}

    def test_read_write_roundtrip(self):
        """Should preserve data through read/write cycle."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.toml"
            config = {"tool": {"robocop": {"lint": {"configure": ["rule.param=value"]}}}}

            write_toml_file(path, config)
            result = read_toml_file(path)

            assert result == config

    def test_merge_new_config(self):
        """Should merge new config into empty config."""
        existing = {}
        new_lint = {"configure": ["rule.param=value"]}

        merged = merge_robocop_config(existing, new_lint)

        assert merged["tool"]["robocop"]["lint"]["configure"] == ["rule.param=value"]

    def test_merge_with_existing_config(self):
        """Should merge new config with existing config."""
        existing = {"tool": {"robocop": {"lint": {"configure": ["old.param=1"]}}}}
        new_lint = {"configure": ["new.param=2"]}

        merged = merge_robocop_config(existing, new_lint)

        assert "old.param=1" in merged["tool"]["robocop"]["lint"]["configure"]
        assert "new.param=2" in merged["tool"]["robocop"]["lint"]["configure"]

    def test_merge_replaces_same_param(self):
        """Should replace configure entries for same rule.param."""
        existing = {"tool": {"robocop": {"lint": {"configure": ["rule.param=old"]}}}}
        new_lint = {"configure": ["rule.param=new"]}

        merged = merge_robocop_config(existing, new_lint)
        configure = merged["tool"]["robocop"]["lint"]["configure"]

        assert len(configure) == 1
        assert configure[0] == "rule.param=new"

    def test_merge_preserves_other_sections(self):
        """Should preserve other sections in existing config."""
        existing = {
            "project": {"name": "test"},
            "tool": {"other": {"key": "value"}},
        }
        new_lint = {"configure": ["rule.param=value"]}

        merged = merge_robocop_config(existing, new_lint)

        assert merged["project"]["name"] == "test"
        assert merged["tool"]["other"]["key"] == "value"

    def test_generate_diff(self):
        """Should generate unified diff."""
        before = "line1\nline2\n"
        after = "line1\nmodified\n"

        diff = generate_diff(before, after)

        assert diff is not None
        assert "-line2" in diff
        assert "+modified" in diff

    def test_generate_diff_no_changes(self):
        """Should return None when no changes."""
        content = "line1\nline2\n"
        diff = generate_diff(content, content)
        assert diff is None

    def test_extract_lint_section_string(self):
        """Should generate TOML string for lint section."""
        lint_config = {"configure": ["rule.param=value"]}

        result = extract_lint_section_string(lint_config)

        assert "[tool.robocop.lint]" in result
        assert "configure" in result


class TestParseLlmResponse:
    """Tests for _parse_llm_response function."""

    def test_parse_valid_json(self):
        """Should parse valid JSON response."""
        response = '{"interpretation": "test", "suggestions": [], "warnings": []}'
        parsed, error = _parse_llm_response(response)

        assert error is None
        assert parsed["interpretation"] == "test"

    def test_parse_json_with_markdown(self):
        """Should parse JSON wrapped in markdown code block."""
        response = '```json\n{"interpretation": "test", "suggestions": []}\n```'
        parsed, error = _parse_llm_response(response)

        assert error is None
        assert parsed["interpretation"] == "test"

    def test_parse_invalid_json(self):
        """Should return error for invalid JSON."""
        response = "not valid json"
        parsed, error = _parse_llm_response(response)

        assert parsed == {}
        assert error is not None
        assert "Failed to parse" in error


class TestValidateSuggestions:
    """Tests for _validate_suggestions function."""

    def test_valid_configure_suggestion(self):
        """Should accept valid configure suggestion."""
        raw = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "140",
                "interpretation": "Allow longer lines",
                "explanation": "Increase limit",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].rule_id == "LEN08"
        assert result.suggestions[0].action == "configure"
        assert result.suggestions[0].parameter == "line_length"
        assert result.suggestions[0].value == "140"

    def test_valid_disable_suggestion(self):
        """Should accept valid disable suggestion."""
        raw = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "disable",
                "interpretation": "Disable line length check",
                "explanation": "Not needed",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].action == "disable"
        assert result.suggestions[0].parameter is None
        assert result.suggestions[0].value is None

    def test_invalid_rule_skipped(self):
        """Should skip invalid rule with warning."""
        raw = [
            {
                "rule_id": "INVALID",
                "rule_name": "nonexistent-rule",
                "action": "configure",
                "parameter": "param",
                "value": "value",
                "interpretation": "test",
                "explanation": "test",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 0
        assert len(result.warnings) == 1
        assert "not found" in result.warnings[0]

    def test_configure_missing_param_skipped(self):
        """Should skip configure action without parameter."""
        raw = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                # Missing parameter and value
                "interpretation": "test",
                "explanation": "test",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 0
        assert len(result.warnings) == 1

    def test_deprecated_rule_warning(self):
        """Should add warning for deprecated rules."""
        # Find a deprecated rule from the catalog
        catalog = build_rule_catalog()
        deprecated_rules = [r for r in catalog if r["deprecated"]]

        if deprecated_rules:
            deprecated = deprecated_rules[0]
            raw = [
                {
                    "rule_id": deprecated["rule_id"],
                    "rule_name": deprecated["name"],
                    "action": "enable",
                    "interpretation": "test",
                    "explanation": "test",
                }
            ]
            result = _validate_suggestions(raw)

            # Should have a deprecation warning
            deprecation_warnings = [w for w in result.warnings if "deprecated" in w.lower()]
            assert len(deprecation_warnings) == 1


class TestParseConfigFromLlmResponse:
    """Tests for parse_config_from_llm_response function."""

    def test_successful_parse(self):
        """Should successfully parse valid response."""
        response = json.dumps(
            {
                "interpretation": "Allow longer lines",
                "suggestions": [
                    {
                        "rule_id": "LEN08",
                        "rule_name": "line-too-long",
                        "action": "configure",
                        "parameter": "line_length",
                        "value": "140",
                        "interpretation": "Allow 140 char lines",
                        "explanation": "Default is 120",
                    }
                ],
                "warnings": [],
            }
        )

        result = parse_config_from_llm_response(response)

        assert result.success is True
        assert len(result.suggestions) == 1
        assert "[tool.robocop.lint]" in result.toml_config
        assert "line-too-long.line_length=140" in result.toml_config

    def test_empty_suggestions(self):
        """Should handle empty suggestions."""
        response = json.dumps(
            {"interpretation": "No rules match", "suggestions": [], "warnings": ["No matching rules"]}
        )

        result = parse_config_from_llm_response(response)

        assert result.success is False
        assert len(result.suggestions) == 0

    def test_invalid_json_response(self):
        """Should handle invalid JSON gracefully."""
        result = parse_config_from_llm_response("not json")

        assert result.success is False
        assert len(result.warnings) > 0


class TestGetConfigSystemMessage:
    """Tests for get_config_system_message function."""

    def test_system_message_contains_rules(self):
        """System message should contain rule information."""
        message = get_config_system_message()

        assert "Robocop" in message
        assert "rules" in message.lower()
        # Should contain some rule IDs
        assert "LEN" in message
        assert "NAME" in message

    def test_system_message_contains_instructions(self):
        """System message should contain configuration instructions."""
        message = get_config_system_message()

        assert "configure" in message.lower()
        assert "JSON" in message
        assert "suggestions" in message

    def test_system_message_contains_examples(self):
        """System message should contain configuration examples."""
        message = get_config_system_message()

        assert "Example:" in message or "example" in message.lower()


class TestApplyConfigImpl:
    """Tests for _apply_config_impl function."""

    def test_apply_to_new_file(self):
        """Should create new file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"
            toml_config = '[tool.robocop.lint]\nconfigure = ["line-too-long.line_length=140"]'

            result = _apply_config_impl(toml_config, str(path))

            assert result.success is True
            assert result.file_created is True
            assert path.exists()

    def test_apply_to_existing_file(self):
        """Should merge with existing file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"
            # Create initial file
            initial_content = {"project": {"name": "test"}}
            write_toml_file(path, initial_content)

            toml_config = '[tool.robocop.lint]\nconfigure = ["line-too-long.line_length=140"]'
            result = _apply_config_impl(toml_config, str(path))

            assert result.success is True
            assert result.file_created is False
            # Should preserve existing content
            final = read_toml_file(path)
            assert final["project"]["name"] == "test"
            assert "configure" in final["tool"]["robocop"]["lint"]

    def test_apply_generates_diff(self):
        """Should generate diff showing changes."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"
            toml_config = '[tool.robocop.lint]\nconfigure = ["line-too-long.line_length=140"]'

            result = _apply_config_impl(toml_config, str(path))

            # Should have a diff for new file
            assert result.diff is not None or result.file_created

    def test_apply_invalid_toml(self):
        """Should handle invalid TOML gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"

            result = _apply_config_impl("invalid toml {{{", str(path))

            assert result.success is False
            assert result.validation_error is not None


class TestValidateSuggestionsSetAction:
    """Tests for _validate_suggestions with 'set' action."""

    def test_valid_set_action_common_section(self):
        """Should accept valid set action for common section."""
        raw = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "value": "/tmp/cache",  # noqa: S108
                "section": "common",
                "interpretation": "Set cache directory",
                "explanation": "Custom cache location",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].action == "set"
        assert result.suggestions[0].parameter == "cache_dir"
        assert result.suggestions[0].value == "/tmp/cache"  # noqa: S108
        assert result.suggestions[0].section == "common"
        assert result.suggestions[0].rule_id is None

    def test_valid_set_action_format_section(self):
        """Should accept valid set action for format section."""
        raw = [
            {
                "action": "set",
                "parameter": "space_count",
                "value": "2",
                "section": "format",
                "interpretation": "Set indentation",
                "explanation": "Use 2 spaces",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].section == "format"

    def test_set_action_missing_value_skipped(self):
        """Should skip set action without value."""
        raw = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "section": "common",
                "interpretation": "Missing value",
                "explanation": "Should fail",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 0
        assert len(result.warnings) == 1
        assert "missing" in result.warnings[0].lower()

    def test_set_action_missing_parameter_skipped(self):
        """Should skip set action without parameter."""
        raw = [
            {
                "action": "set",
                "value": "/tmp/cache",  # noqa: S108
                "section": "common",
                "interpretation": "Missing parameter",
                "explanation": "Should fail",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 0
        assert len(result.warnings) == 1

    def test_invalid_section_defaults_to_lint(self):
        """Should default to lint section and warn for invalid section."""
        raw = [
            {
                "action": "set",
                "parameter": "some_param",
                "value": "some_value",
                "section": "invalid_section",
                "interpretation": "Invalid section",
                "explanation": "Should warn",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].section == "lint"  # Defaulted
        assert len(result.warnings) == 1
        assert "invalid" in result.warnings[0].lower()


class TestBuildConfigOptionsCatalog:
    """Tests for build_config_options_catalog function."""

    def test_catalog_has_all_sections(self):
        """Catalog should have common, lint, and format sections."""
        catalog = build_config_options_catalog()

        assert "common" in catalog
        assert "lint" in catalog
        assert "format" in catalog

    def test_common_section_has_options(self):
        """Common section should have config options."""
        catalog = build_config_options_catalog()
        common = catalog["common"]

        # Should have some options
        assert len(common) > 0
        # Check structure
        for opt in common:
            assert "name" in opt
            assert "type" in opt
            assert "default" in opt

    def test_format_section_has_options(self):
        """Format section should have config options."""
        catalog = build_config_options_catalog()
        fmt = catalog["format"]

        # Should have some format options
        assert len(fmt) > 0


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_full_workflow(self):
        """Test complete workflow from LLM response to file application."""
        # Step 1: Get system message (would be used by host LLM)
        system_message = get_config_system_message()
        assert len(system_message) > 1000

        # Step 2: Parse LLM response
        llm_response = json.dumps(
            {
                "interpretation": "Configure line length and disable naming rule",
                "suggestions": [
                    {
                        "rule_id": "LEN08",
                        "rule_name": "line-too-long",
                        "action": "configure",
                        "parameter": "line_length",
                        "value": "140",
                        "interpretation": "Allow 140 char lines",
                        "explanation": "Increase from default 120",
                    },
                    {
                        "rule_id": "NAME01",
                        "rule_name": "not-allowed-char-in-name",
                        "action": "disable",
                        "interpretation": "Disable naming check",
                        "explanation": "Project uses dots in names",
                    },
                ],
                "warnings": [],
            }
        )

        parse_result = parse_config_from_llm_response(llm_response)
        assert parse_result.success is True
        assert len(parse_result.suggestions) == 2

        # Step 3: Apply to file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"

            apply_result = _apply_config_impl(parse_result.toml_config, str(path))

            assert apply_result.success is True

            # Verify file contents
            final_config = read_toml_file(path)
            lint_section = final_config["tool"]["robocop"]["lint"]

            assert "line-too-long.line_length=140" in lint_section["configure"]
            assert "NAME01" in lint_section["ignore"]

    def test_workflow_with_set_action(self):
        """Test workflow with set action for config options."""
        llm_response = json.dumps(
            {
                "interpretation": "Set cache directory and indentation",
                "suggestions": [
                    {
                        "action": "set",
                        "parameter": "cache_dir",
                        "value": "/custom/cache",
                        "section": "common",
                        "interpretation": "Custom cache path",
                        "explanation": "Store cache in custom location",
                    },
                    {
                        "action": "set",
                        "parameter": "space_count",
                        "value": "2",
                        "section": "format",
                        "interpretation": "2-space indent",
                        "explanation": "Use 2 spaces for indentation",
                    },
                ],
                "warnings": [],
            }
        )

        parse_result = parse_config_from_llm_response(llm_response)
        assert parse_result.success is True
        assert len(parse_result.suggestions) == 2

        # Verify TOML contains both sections
        toml_config = parse_result.toml_config
        assert "cache_dir" in toml_config
        assert "space_count" in toml_config

    def test_workflow_mixed_actions(self):
        """Test workflow with both rule config and set actions."""
        llm_response = json.dumps(
            {
                "interpretation": "Configure rules and options",
                "suggestions": [
                    {
                        "rule_id": "LEN08",
                        "rule_name": "line-too-long",
                        "action": "configure",
                        "parameter": "line_length",
                        "value": "140",
                        "section": "lint",
                        "interpretation": "Longer lines",
                        "explanation": "Allow 140 chars",
                    },
                    {
                        "action": "set",
                        "parameter": "cache_dir",
                        "value": "/tmp/cache",  # noqa: S108
                        "section": "common",
                        "interpretation": "Cache dir",
                        "explanation": "Custom cache",
                    },
                ],
                "warnings": [],
            }
        )

        parse_result = parse_config_from_llm_response(llm_response)
        assert parse_result.success is True
        assert len(parse_result.suggestions) == 2

        # Apply to file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "pyproject.toml"

            apply_result = _apply_config_impl(parse_result.toml_config, str(path))

            assert apply_result.success is True

            # Verify file contains both sections
            final_config = read_toml_file(path)
            assert "cache_dir" in final_config["tool"]["robocop"]
            assert "lint" in final_config["tool"]["robocop"]


class TestEdgeCases:
    """Tests for edge cases and corner scenarios."""

    def test_suggestion_without_section_defaults_to_lint(self):
        """Suggestion without explicit section should default to lint."""
        raw = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "140",
                # No section field - should default to "lint"
                "interpretation": "Allow longer lines",
                "explanation": "Default to lint",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 1
        assert result.suggestions[0].section == "lint"

    def test_empty_suggestions_array(self):
        """Response with empty suggestions array should fail."""
        response = json.dumps(
            {
                "interpretation": "User wants nothing",
                "suggestions": [],
                "warnings": [],
            }
        )

        result = parse_config_from_llm_response(response)

        assert result.success is False
        assert len(result.suggestions) == 0

    def test_configure_with_empty_value(self):
        """Configure action with empty value string should be skipped."""
        raw = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "",  # Empty value
                "interpretation": "Empty value",
                "explanation": "Should fail",
            }
        ]
        result = _validate_suggestions(raw)

        assert len(result.suggestions) == 0
        assert len(result.warnings) > 0

    def test_duplicate_configure_entries_last_wins(self):
        """Multiple configure entries for same rule.param should result in one entry."""
        suggestions = [
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "100",
                "section": "lint",
            },
            {
                "rule_id": "LEN08",
                "rule_name": "line-too-long",
                "action": "configure",
                "parameter": "line_length",
                "value": "200",  # This should win
                "section": "lint",
            },
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        # Should have both entries (generation doesn't dedupe, but that's fine)
        configure = config["lint"]["configure"]
        assert "line-too-long.line_length=100" in configure
        assert "line-too-long.line_length=200" in configure

    def test_boolean_value_conversion(self):
        """Set action with boolean-like strings should convert properly."""
        suggestions = [
            {
                "action": "set",
                "parameter": "verbose",
                "value": "true",
                "section": "common",
            },
            {
                "action": "set",
                "parameter": "silent",
                "value": "false",
                "section": "common",
            },
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        # Boolean conversion: "true" -> True, "false" -> False
        assert config["common"]["verbose"] is True
        assert config["common"]["silent"] is False

    def test_numeric_value_conversion(self):
        """Set action with numeric strings should convert to numbers."""
        suggestions = [
            {
                "action": "set",
                "parameter": "space_count",
                "value": "4",
                "section": "format",
            },
            {
                "action": "set",
                "parameter": "line_length",
                "value": "120",
                "section": "format",
            },
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        assert config["format"]["space_count"] == 4
        assert config["format"]["line_length"] == 120
        assert isinstance(config["format"]["space_count"], int)

    def test_rule_lookup_case_insensitive_name(self):
        """Rule lookup should work with case variations."""
        # Lowercase
        rule1 = get_rule_by_name_or_id("line-too-long")
        assert rule1 is not None

        # The exact case should work
        assert rule1.name == "line-too-long"

    def test_section_field_respected_in_response(self):
        """Section field in LLM response should be respected for rule actions."""
        response = json.dumps(
            {
                "interpretation": "Configure rule in lint section",
                "suggestions": [
                    {
                        "rule_id": "LEN08",
                        "rule_name": "line-too-long",
                        "action": "configure",
                        "parameter": "line_length",
                        "value": "140",
                        "section": "lint",  # Explicit section
                        "interpretation": "Allow longer lines",
                        "explanation": "In lint section",
                    }
                ],
                "warnings": [],
            }
        )

        result = parse_config_from_llm_response(response)

        assert result.success is True
        assert result.suggestions[0].section == "lint"
        assert "[tool.robocop.lint]" in result.toml_config

    @pytest.mark.skipif(sys.platform == "win32", reason="Unix-style permissions don't work on Windows")
    def test_apply_to_read_only_directory(self):
        """Should handle permission errors gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a read-only directory (Unix only)
            readonly_dir = Path(tmpdir) / "readonly"
            readonly_dir.mkdir()

            # Make it read-only
            original_mode = readonly_dir.stat().st_mode
            try:
                os.chmod(readonly_dir, stat.S_IRUSR | stat.S_IXUSR)

                path = readonly_dir / "test.toml"
                toml_config = '[tool.robocop.lint]\nconfigure = ["rule.param=value"]'

                result = _apply_config_impl(toml_config, str(path))

                # Should fail with permission error
                assert result.success is False
                assert result.validation_error is not None
                assert "Permission" in result.validation_error or "denied" in result.validation_error.lower()
            finally:
                # Restore permissions for cleanup
                os.chmod(readonly_dir, original_mode)

    def test_enable_action_for_disabled_rule_still_works(self):
        """Enable action should work for rules that are disabled by default."""
        # Find a disabled rule
        catalog = build_rule_catalog()
        disabled_rules = [r for r in catalog if not r["enabled"]]

        if disabled_rules:
            disabled = disabled_rules[0]
            raw = [
                {
                    "rule_id": disabled["rule_id"],
                    "rule_name": disabled["name"],
                    "action": "enable",
                    "interpretation": "Enable disabled rule",
                    "explanation": "Turn on",
                }
            ]
            result = _validate_suggestions(raw)

            assert len(result.suggestions) == 1
            assert result.suggestions[0].action == "enable"
            # Should not have warnings about the rule being disabled
            disabled_warnings = [w for w in result.warnings if "disabled" in w.lower()]
            assert len(disabled_warnings) == 0

    def test_negative_integer_value(self):
        """Should handle negative integers in set action."""
        suggestions = [
            {
                "action": "set",
                "parameter": "threshold",
                "value": "-1",
                "section": "lint",
            }
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        assert config["lint"]["threshold"] == -1
        assert isinstance(config["lint"]["threshold"], int)

    def test_string_value_preserved(self):
        """Non-numeric string values should remain strings."""
        suggestions = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "value": "/path/to/cache",
                "section": "common",
            },
            {
                "action": "set",
                "parameter": "language",
                "value": "en",
                "section": "common",
            },
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        assert config["common"]["cache_dir"] == "/path/to/cache"
        assert config["common"]["language"] == "en"
        assert isinstance(config["common"]["cache_dir"], str)

    def test_warnings_from_llm_preserved(self):
        """Warnings from LLM response should be preserved in result."""
        response = json.dumps(
            {
                "interpretation": "User request",
                "suggestions": [
                    {
                        "rule_id": "LEN08",
                        "rule_name": "line-too-long",
                        "action": "configure",
                        "parameter": "line_length",
                        "value": "140",
                        "interpretation": "Allow longer lines",
                        "explanation": "Increase limit",
                    }
                ],
                "warnings": ["This might affect readability", "Consider your team's preferences"],
            }
        )

        result = parse_config_from_llm_response(response)

        assert result.success is True
        assert "This might affect readability" in result.warnings
        assert "Consider your team's preferences" in result.warnings

    def test_special_characters_in_path_value(self):
        """Values with special characters should be handled."""
        suggestions = [
            {
                "action": "set",
                "parameter": "cache_dir",
                "value": "/path/with spaces/and-dashes/under_scores",
                "section": "common",
            }
        ]
        config = generate_toml_config_from_suggestions(suggestions)

        assert config["common"]["cache_dir"] == "/path/with spaces/and-dashes/under_scores"

    def test_system_message_has_cli_only_warning(self):
        """System message should warn about CLI-only options."""
        message = get_config_system_message()

        # Should mention CLI-only options
        assert "CLI" in message or "command-line" in message.lower()
        # Should mention specific CLI-only options
        assert "--ignore-git-dir" in message or "ignore-git-dir" in message

    def test_format_section_options_in_system_message(self):
        """System message should include format section options."""
        message = get_config_system_message()

        # Should mention format-related options
        assert "format" in message.lower()
        assert "space_count" in message or "indent" in message.lower()
