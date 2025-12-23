"""Tests for MCP resources."""

from robocop.mcp.resources import (
    _get_formatters_catalog,
    _get_rule_details,
    _get_rules_catalog,
)


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


class TestRuleDetails:
    """Tests for rule details resource."""

    def test_get_rule_details(self):
        """Test getting detailed rule info."""
        result = _get_rule_details("LEN01")
        assert result["rule_id"] == "LEN01"
        assert "name" in result
        assert "docs" in result
        assert "parameters" in result

    def test_get_nonexistent_rule_details(self):
        """Test getting details for nonexistent rule."""
        result = _get_rule_details("NONEXISTENT")
        assert "error" in result
