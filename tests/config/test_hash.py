from robocop.config.builder import ConfigBuilder
from robocop.config.schema import (
    FormatterConfig,
    LinterConfig,
    RawFormatterConfig,
    RawLinterConfig,
    RawWhitespaceConfig,
)
from robocop.linter.rules import RuleSeverity
from robocop.version_handling import ROBOT_VERSION, Version


def get_linter_config(**kwargs) -> LinterConfig:
    target_version = kwargs.pop("target_version", ROBOT_VERSION)
    cli_raw = RawLinterConfig(**kwargs)
    return ConfigBuilder().linter_from_raw(cli_raw, None, target_version, silent=False)


def get_formatter_config(**kwargs) -> FormatterConfig:
    target_version = kwargs.pop("target_version", ROBOT_VERSION)
    cli_raw = RawFormatterConfig(**kwargs)
    return ConfigBuilder().formatter_from_raw(cli_raw, None, target_version, languages=None, silent=False)


class TestLinterConfigHash:
    """Test __hash__ on LinterConfig for cache invalidation."""

    def test_linter_config_hash_consistency(self):
        config1 = get_linter_config(select=["DOC01", "DOC02"])
        config2 = get_linter_config(select=["DOC01", "DOC02"])

        assert config1.hash == config2.hash

    def test_linter_config_hash_changes_on_select(self):
        config1 = get_linter_config(select=["DOC01"])
        config2 = get_linter_config(select=["DOC02"])

        assert config1.hash != config2.hash

    def test_linter_config_hash_changes_on_ignore(self):
        config1 = get_linter_config(ignore=["DOC01"])
        config2 = get_linter_config(ignore=["DOC02"])

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_changes_on_extend_select(self):
        config1 = get_linter_config(extend_select=["DOC01"])
        config2 = get_linter_config(extend_select=["DOC02"])

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_changes_on_threshold(self):
        config1 = get_linter_config(threshold=RuleSeverity.WARNING)
        config2 = get_linter_config(threshold=RuleSeverity.ERROR)

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_changes_on_configure(self):
        config1 = get_linter_config(configure=["rule.param=value1"])
        config2 = get_linter_config(configure=["rule.param=value2"])

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_changes_on_per_file_ignores(self):
        config1 = get_linter_config(per_file_ignores={"*.robot": ["DOC01"]})
        config2 = get_linter_config(per_file_ignores={"*.robot": ["DOC02"]})

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_select_order_independent(self):
        config1 = get_linter_config(select=["DOC01", "DOC02"])
        config2 = get_linter_config(select=["DOC02", "DOC01"])

        assert hash(config1) == hash(config2)  # Order should not matter

    def test_linter_config_hash_changes_on_target_version(self):
        config1 = get_linter_config(target_version=Version("6.0"))
        config2 = get_linter_config(target_version=Version("7.0"))

        assert hash(config1) != hash(config2)

    def test_linter_config_hash_changes_on_custom_rules(self):
        config1 = get_linter_config(custom_rules=["/path/to/rules1.py"])
        config2 = get_linter_config(custom_rules=["/path/to/rules2.py"])

        assert hash(config1) != hash(config2)


class TestFormatterConfigHash:
    """Test __hash__ on FormatterConfig for cache invalidation."""

    def test_formatter_config_hash_consistency(self):
        config1 = get_formatter_config()
        config2 = get_formatter_config()

        assert hash(config1) == hash(config2)

    def test_formatter_config_hash_changes_on_select(self):
        config1 = get_formatter_config(select=["NormalizeSeparators"])
        config2 = get_formatter_config(select=["AlignSettingsSection"])

        assert hash(config1) != hash(config2)

    def test_formatter_config_hash_changes_on_whitespace(self):
        config1 = get_formatter_config(whitespace_config=RawWhitespaceConfig(space_count=4))
        config2 = get_formatter_config(whitespace_config=RawWhitespaceConfig(space_count=2))

        assert hash(config1) != hash(config2)

    def test_formatter_config_hash_changes_on_target_version(self):
        config1 = get_formatter_config(target_version=Version("6.0"))
        config2 = get_formatter_config(target_version=Version("7.0"))

        assert hash(config1) != hash(config2)

    def test_formatter_config_hash_select_order_independent(self):
        config1 = get_formatter_config(select=["NormalizeSeparators", "AlignSettingsSection"])
        config2 = get_formatter_config(select=["AlignSettingsSection", "NormalizeSeparators"])

        assert hash(config1) == hash(config2)  # Order should not matter
