"""Tests for MCP caching module."""

from robocop.mcp.cache import clear_cache, get_formatter_config, get_linter_config


class TestCache:
    """Tests for configuration caching."""

    def teardown_method(self):
        """Clear cache after each test."""
        clear_cache()

    def test_linter_config_cached(self):
        """Test that linter config is cached and returns same instance."""
        config1 = get_linter_config(None)
        config2 = get_linter_config(None)
        assert config1 is config2

    def test_formatter_config_cached(self):
        """Test that formatter config is cached and returns same instance."""
        config1 = get_formatter_config(None)
        config2 = get_formatter_config(None)
        assert config1 is config2

    def test_linter_config_has_rules(self):
        """Test that linter config has rules loaded."""
        config = get_linter_config(None)
        assert len(config.rules) > 0

    def test_formatter_config_has_formatters(self):
        """Test that formatter config has formatters loaded."""
        config = get_formatter_config(None)
        assert len(config.formatters) > 0

    def test_clear_cache_resets_configs(self):
        """Test that clear_cache allows new instances to be created."""
        config1 = get_linter_config(None)
        clear_cache()
        config2 = get_linter_config(None)
        assert config1 is not config2
