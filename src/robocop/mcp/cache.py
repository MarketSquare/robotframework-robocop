"""Cached configuration for MCP server - avoids reloading rules/formatters on each call."""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robocop.runtime.resolved_config import ResolvedConfig


@lru_cache(maxsize=1)
def get_linter_config() -> ResolvedConfig:
    """
    Get cached LinterConfig with all rules loaded.

    The config is created and cached on first call, then reused for subsequent calls.
    This avoids the overhead of discovering and loading 160+ rules on every request.

    Returns:
        LinterConfig: The cached linter configuration with rules loaded.

    """
    from robocop.config.manager import ConfigManager
    from robocop.runtime.resolver import ConfigResolver

    manager = ConfigManager()
    resolver = ConfigResolver(load_rules=True)

    return resolver.resolve_config(manager.default_config)


@lru_cache(maxsize=1)
def get_formatter_config() -> ResolvedConfig:
    """
    Get cached FormatterConfig with all formatters loaded.

    The config is created and cached on first call, then reused for subsequent calls.
    This avoids the overhead of discovering and loading formatters on every request.

    Returns:
        FormatterConfig: The cached formatter configuration with formatters loaded.

    """
    from robocop.config.manager import ConfigManager
    from robocop.runtime.resolver import ConfigResolver

    manager = ConfigManager()
    resolver = ConfigResolver(load_formatters=True)

    return resolver.resolve_config(manager.default_config)


def clear_cache() -> None:
    """
    Clear the cached configurations.

    Useful for testing or when you need to reload rules/formatters.
    """
    get_linter_config.cache_clear()
    get_formatter_config.cache_clear()
