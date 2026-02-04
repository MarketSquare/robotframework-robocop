"""
Functions for calculating configuration hash.

Hash is used in caching to determine whether the configuration file used
when linting / formatting has changed since the last run.
"""

from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from robocop.config.schema import WhitespaceConfig
    from robocop.linter.rules import RuleSeverity
    from robocop.version_handling import Version


def _sorted_tuple(items: list[str] | None) -> tuple[str, ...]:
    """
    Convert list to sorted tuple, handling None.

    Returns:
        A sorted tuple representation of the input list.

    """
    return tuple(sorted(items or []))


def _dict_of_list_str(value: dict[str, list[str]]) -> str:
    """
    Create a string representation of a dictionary with a list of str as values.

    Returns:
        A string representation of dictionary or empty string if None.

    """
    if not value:
        return ""
    items = sorted((key, ":".join(sorted(values))) for key, values in value.items())
    return ";".join(f"{key}={values}" for key, values in items)


def linter_hash(
    select: list[str],
    extend_select: list[str],
    ignore: list[str],
    configure: list[str],
    custom_rules: list[str],
    threshold: RuleSeverity,
    target_version: Version,
    per_file_ignores: dict[str, list[str]],
) -> int:
    """
    Hash of configuration options that affect linting results.

    Used for cache invalidation - if configuration changes, cached results are invalidated.
    Note: This makes LinterConfig usable as a dict key, but only hash config-affecting fields.

    Uses stable hashing (SHA256) to ensure consistent hashes across Python process restarts,
    avoiding issues with Python's hash randomization (PEP 456).

    Returns:
        Hash value of the configuration options.

    """
    # Build a stable string representation of the config
    config_parts = [
        ":".join(_sorted_tuple(select)),
        ":".join(_sorted_tuple(extend_select)),
        ":".join(_sorted_tuple(ignore)),
        ":".join(_sorted_tuple(configure)),
        ":".join(_sorted_tuple(custom_rules)),
        str(threshold),
        str(target_version),
        _dict_of_list_str(per_file_ignores),
    ]
    config_str = "|".join(config_parts)

    # Use SHA256 for stable hashing, then convert to int for __hash__ return type
    hash_bytes = hashlib.sha256(config_str.encode("utf-8")).digest()
    # Convert the first 8 bytes to int for hash compatibility
    return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)


def formatter_hash(
    select: list[str],
    extend_select: list[str],
    configure: list[str],
    target_version: Version,
    whitespace_config: WhitespaceConfig,
) -> int:
    """
    Hash of configuration options that affect formatting results.

    Used for cache invalidation - if configuration changes, cached results are invalidated.
    Note: This makes FormatterConfig usable as dict key, but only hash config-affecting fields.

    Uses stable hashing (SHA256) to ensure consistent hashes across Python process restarts,
    avoiding issues with Python's hash randomization (PEP 456).

    Returns:
        Hash value of the configuration options.

    """
    # Build a stable string representation of the config
    config_parts = [
        ":".join(_sorted_tuple(select)),
        ":".join(_sorted_tuple(extend_select)),
        ":".join(_sorted_tuple(configure)),
        str(target_version),
        str(whitespace_config.space_count),
        str(whitespace_config.indent),
        str(whitespace_config.continuation_indent),
        str(whitespace_config.separator),
        str(whitespace_config.line_ending),
        str(whitespace_config.line_length),
    ]
    config_str = "|".join(config_parts)

    # Use SHA256 for stable hashing, then convert to int for __hash__ return type
    hash_bytes = hashlib.sha256(config_str.encode("utf-8")).digest()
    # Convert the first 8 bytes to int for hash compatibility
    return int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)


def config_hash(lint_hash: int, format_hash: int, language: list[str]) -> str:
    hasher = hashlib.sha256()
    hasher.update(str(hash(lint_hash)).encode("utf-8"))
    hasher.update(str(hash(format_hash)).encode("utf-8"))
    language_str = ":".join(sorted(language))
    hasher.update(language_str.encode("utf-8"))
    return hasher.hexdigest()
