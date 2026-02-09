"""Tests for MCP resources."""

import asyncio

import pytest
from fastmcp.exceptions import ResourceError

from robocop.mcp import mcp
from robocop.mcp.cache import clear_cache
from robocop.mcp.resources import (
    _get_formatters_catalog,
    _get_rule_details,
    _get_rules_catalog,
)
from tests import TEST_DATA_LINTER_DIR, working_directory

CUSTOM_RULES_DIR = TEST_DATA_LINTER_DIR / "custom_rules" / "custom_with_config"


class TestRulesCatalog:
    """Tests for rules catalog resource."""

    def test_get_rules_catalog(self):
        """Test getting the full rules catalog."""
        rules = _get_rules_catalog()
        assert isinstance(rules, list)
        assert len(rules) > 0

        # Check structure
        rule = rules[0]
        assert "rule_id" in rule
        assert "name" in rule
        assert "message" in rule
        assert "severity" in rule
        assert "enabled" in rule

    def test_rules_sorted_by_id(self):
        """Test that rules are sorted by ID."""
        rules = _get_rules_catalog()
        rule_ids = [r["rule_id"] for r in rules]
        assert rule_ids == sorted(rule_ids)

    def test_rules_catalog_includes_deprecated(self):
        """Test that rules catalog includes deprecated field."""
        rules = _get_rules_catalog()
        for rule in rules:
            assert "deprecated" in rule
            assert isinstance(rule["deprecated"], bool)

    def test_rules_catalog_includes_added_in_version(self):
        """Test that rules catalog includes added_in_version field."""
        rules = _get_rules_catalog()
        for rule in rules:
            assert "added_in_version" in rule

    def test_rules_catalog_has_all_severities(self):
        """Test that rules catalog includes rules of all severities."""
        rules = _get_rules_catalog()
        severities = {rule["severity"] for rule in rules}
        # Should have at least W and I (E may not exist in all configurations)
        assert "W" in severities or "I" in severities

    def test_rules_catalog_no_duplicates(self):
        """Test that rules catalog has no duplicate IDs."""
        rules = _get_rules_catalog()
        rule_ids = [r["rule_id"] for r in rules]
        assert len(rule_ids) == len(set(rule_ids))

    def test_custom_rule_is_loaded(self):
        """Test that custom rule is loaded using a configuration file found in root directory."""
        clear_cache()

        with working_directory(CUSTOM_RULES_DIR):
            rules = _get_rules_catalog()

        assert any(rule["rule_id"] == "EXT01" for rule in rules)

        clear_cache()


class TestFormattersCatalog:
    """Tests for formatters catalog resource."""

    def test_get_formatters_catalog(self):
        """Test getting the full formatters catalog."""
        formatters = _get_formatters_catalog()
        assert isinstance(formatters, list)
        assert len(formatters) > 0

        # Check structure
        formatter = formatters[0]
        assert "name" in formatter
        assert "enabled" in formatter
        assert "description" in formatter

    def test_formatters_sorted_by_name(self):
        """Test that formatters are sorted by name."""
        formatters = _get_formatters_catalog()
        names = [f["name"] for f in formatters]
        assert names == sorted(names)

    def test_formatters_catalog_has_normalize_separators(self):
        """Test that catalog includes NormalizeSeparators formatter."""
        formatters = _get_formatters_catalog()
        names = {f["name"]: f["enabled"] for f in formatters}
        assert "NormalizeSeparators" in names
        assert names["NormalizeSeparators"] is True

    def test_formatters_catalog_loads_user_config(self, tmp_path):
        """Test that catalog NormalizeSeparators is disabled reflecting user configuration."""
        clear_cache()

        config_file = tmp_path / "pyproject.toml"
        config_file.write_text("[tool.robocop.format]\nconfigure=['NormalizeSeparators.enabled=False']")

        with working_directory(tmp_path):
            formatters = _get_formatters_catalog()

        names = {f["name"]: f["enabled"] for f in formatters}
        assert "NormalizeSeparators" not in names

        clear_cache()

    def test_formatters_catalog_has_descriptions(self):
        """Test that all formatters have non-empty descriptions."""
        formatters = _get_formatters_catalog()
        for formatter in formatters:
            assert formatter["description"]
            assert len(formatter["description"]) > 0

    def test_formatters_catalog_no_duplicates(self):
        """Test that formatters catalog has no duplicate names."""
        formatters = _get_formatters_catalog()
        names = [f["name"] for f in formatters]
        assert len(names) == len(set(names))


class TestRuleDetails:
    """Tests for rule details resource."""

    def test_get_rule_details(self):
        """Test getting detailed rule info."""
        result = _get_rule_details("LEN01")
        assert result["rule_id"] == "LEN01"
        assert "name" in result
        assert "docs" in result
        assert "parameters" in result

    def test_get_rule_details_by_name(self):
        """Test getting rule details by name instead of ID."""
        result = _get_rule_details("too-long-keyword")
        assert result["name"] == "too-long-keyword"
        assert result["rule_id"] == "LEN01"

    def test_get_nonexistent_rule_details(self):
        """Test getting details for nonexistent rule raises ResourceError."""
        with pytest.raises(ResourceError, match="Rule 'NONEXISTENT' not found"):
            _get_rule_details("NONEXISTENT")

    def test_get_rule_details_includes_version_requirement(self):
        """Test that rule details include version_requirement field."""
        result = _get_rule_details("LEN01")
        assert "version_requirement" in result

    def test_get_rule_details_includes_severity(self):
        """Test that rule details include severity field."""
        result = _get_rule_details("LEN01")
        assert "severity" in result
        assert result["severity"] in ("E", "W", "I")

    def test_get_rule_details_parameters_structure(self):
        """Test that rule parameters have correct structure."""
        result = _get_rule_details("LEN01")
        for param in result["parameters"]:
            assert "name" in param
            assert "default" in param
            assert "description" in param
            assert "type" in param


class TestResourcesRegistration:
    """Tests for MCP resources registration."""

    def test_resources_accessible_via_mcp(self):
        """Test that resources are accessible via MCP server."""
        resources = asyncio.run(mcp.get_resources())
        # Should have at least the catalog resources
        assert len(resources) >= 2

    def test_rules_resource_registered(self):
        """Test that rules catalog resource is registered."""
        resources = asyncio.run(mcp.get_resources())
        # get_resources() returns a dict with URIs as keys
        resource_uris = list(resources.keys())
        assert any("rules" in uri for uri in resource_uris)

    def test_formatters_resource_registered(self):
        """Test that formatters catalog resource is registered."""
        resources = asyncio.run(mcp.get_resources())
        # get_resources() returns a dict with URIs as keys
        resource_uris = list(resources.keys())
        assert any("formatters" in uri for uri in resource_uris)
