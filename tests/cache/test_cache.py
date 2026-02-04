"""Tests for file-level caching functionality."""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock

import msgpack
import pytest

from robocop import __version__
from robocop.cache import (
    CacheData,
    CachedDiagnostic,
    FileMetadata,
    FormatterCacheEntry,
    LinterCacheEntry,
    RobocopCache,
    restore_diagnostics,
)
from robocop.config.defaults import CACHE_DIR_NAME, CACHE_FILE_NAME
from robocop.config.schema import RawCacheConfig
from robocop.linter.diagnostics import Diagnostic
from robocop.linter.rules import RuleSeverity
from robocop.runtime.resolved_config import ResolvedConfig
from robocop.source_file import SourceFile


class TestFileMetadata:
    def test_from_path(self, tmp_path: Path):
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        metadata = FileMetadata.from_path(test_file)

        assert metadata.mtime > 0
        assert metadata.size == 7  # len("content")

    def test_frozen(self, tmp_path: Path):
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")
        metadata = FileMetadata.from_path(test_file)

        with pytest.raises(AttributeError):
            metadata.mtime = 0


class TestCachedDiagnostic:
    def test_to_dict(self):
        cached = CachedDiagnostic(
            rule_id="DOC01",
            rule_name="missing-doc-keyword",
            line=10,
            col=1,
            end_line=10,
            end_col=5,
            severity="W",
            arguments=(("name", "My Keyword"),),
        )

        result = cached.to_dict()

        assert result == {
            "rule_id": "DOC01",
            "rule_name": "missing-doc-keyword",
            "line": 10,
            "col": 1,
            "end_line": 10,
            "end_col": 5,
            "severity": "W",
            "arguments": {"name": "My Keyword"},
        }

    def test_from_dict(self):
        data = {
            "rule_id": "DOC01",
            "rule_name": "missing-doc-keyword",
            "line": 10,
            "col": 1,
            "end_line": 10,
            "end_col": 5,
            "severity": "W",
            "arguments": {"name": "My Keyword"},
        }

        cached = CachedDiagnostic.from_dict(data)

        assert cached.rule_id == "DOC01"
        assert cached.rule_name == "missing-doc-keyword"
        assert cached.line == 10
        assert cached.severity == "W"
        assert dict(cached.arguments) == {"name": "My Keyword"}


class TestLinterCacheEntry:
    def test_to_dict(self):
        entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=1234567890.0, size=100),
            config_hash="abc123",
            diagnostics=(),
        )

        result = entry.to_dict()

        assert result["mtime"] == 1234567890.0
        assert result["size"] == 100
        assert result["config_hash"] == "abc123"
        assert result["diagnostics"] == []

    def test_from_dict(self):
        data = {
            "mtime": 1234567890.0,
            "size": 100,
            "config_hash": "abc123",
            "diagnostics": [],
        }

        entry = LinterCacheEntry.from_dict(data)

        assert entry.metadata.mtime == 1234567890.0
        assert entry.metadata.size == 100
        assert entry.config_hash == "abc123"
        assert entry.diagnostics == ()


class TestFormatterCacheEntry:
    def test_to_dict(self):
        entry = FormatterCacheEntry(
            metadata=FileMetadata(mtime=1234567890.0, size=100),
            config_hash="def456",
            needs_formatting=False,
        )

        result = entry.to_dict()

        assert result["mtime"] == 1234567890.0
        assert result["size"] == 100
        assert result["config_hash"] == "def456"
        assert result["needs_formatting"] is False

    def test_from_dict(self):
        data = {
            "mtime": 1234567890.0,
            "size": 100,
            "config_hash": "def456",
            "needs_formatting": True,
        }

        entry = FormatterCacheEntry.from_dict(data)

        assert entry.metadata.mtime == 1234567890.0
        assert entry.config_hash == "def456"
        assert entry.needs_formatting is True


class TestCacheData:
    def test_to_dict(self):
        cache_data = CacheData()

        result = cache_data.to_dict()

        assert result["robocop_version"] == __version__
        assert result["linter"] == {}
        assert result["formatter"] == {}

    def test_from_dict(self):
        data = {
            "version": "1.0",  # deprecated, left for backward compatibility test
            "robocop_version": "7.0.0",
            "linter": {},
            "formatter": {},
        }

        cache_data = CacheData.from_dict(data)

        assert cache_data.robocop_version == "7.0.0"


class TestRobocopCache:
    def test_load_from_existing_file(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache_dir.mkdir()
        cache_file = cache_dir / CACHE_FILE_NAME
        cache_file.write_bytes(
            msgpack.packb(
                {
                    "robocop_version": __version__,
                    "linter": {
                        "/path/to/file.robot": {
                            "mtime": 1234567890.0,
                            "size": 100,
                            "config_hash": "abc",
                            "diagnostics": [],
                        }
                    },
                    "formatter": {},
                },
                use_bin_type=True,
            )
        )

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        assert "/path/to/file.robot" in cache.data.linter

    def test_load_invalidates_on_version_mismatch(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache_dir.mkdir()
        cache_file = cache_dir / CACHE_FILE_NAME
        cache_file.write_bytes(
            msgpack.packb(
                {
                    "robocop_version": "0.0.0",  # Different version
                    "linter": {
                        "/path/to/file.robot": {
                            "mtime": 123,
                            "size": 1,
                            "config_hash": "x",
                            "diagnostics": [],
                        }
                    },
                    "formatter": {},
                },
                use_bin_type=True,
            )
        )

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        # Cache should be cleared due to version mismatch
        assert cache.data.linter == {}

    def test_load_handles_corrupted_cache(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache_dir.mkdir()
        cache_file = cache_dir / CACHE_FILE_NAME
        cache_file.write_bytes(b"not valid msgpack data")

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        # Should create empty cache
        assert cache.data.linter == {}
        assert cache.data.formatter == {}

    def test_save(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        # Create a test file
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        # Add entry
        cache.set_linter_entry(test_file, "hash123", [])
        cache.save()

        # Verify file exists
        cache_file = cache_dir / CACHE_FILE_NAME
        assert cache_file.exists()

        # Verify content
        data = msgpack.unpackb(cache_file.read_bytes(), raw=False, strict_map_key=False)
        assert str(test_file.resolve()) in data["linter"]

    def test_save_does_nothing_when_disabled(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache = RobocopCache(cache_dir=cache_dir, enabled=False, verbose=False)

        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash", [])
        cache.save()

        assert not cache_dir.exists()

    def test_get_linter_entry_valid(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash123", [])
        entry = cache.get_linter_entry(test_file, "hash123")

        assert entry is not None
        assert entry.config_hash == "hash123"

    def test_get_linter_entry_invalid_mtime(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash123", [])

        # Modify the file (changes mtime)
        test_file.write_text("new content")

        entry = cache.get_linter_entry(test_file, "hash123")

        # Entry should be invalidated
        assert entry is None

    def test_get_linter_entry_invalid_config_hash(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash123", [])
        entry = cache.get_linter_entry(test_file, "different_hash")

        # Entry should be invalidated due to config hash mismatch
        assert entry is None

    def test_get_linter_entry_returns_none_when_disabled(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=False, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        entry = cache.get_linter_entry(test_file, "hash123")

        assert entry is None

    def test_get_formatter_entry_valid(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_formatter_entry(test_file, "hash123", needs_formatting=False)
        entry = cache.get_formatter_entry(test_file, "hash123")

        assert entry is not None
        assert entry.needs_formatting is False

    def test_invalidate_all(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash", [])
        cache.set_formatter_entry(test_file, "hash", needs_formatting=True)

        cache.invalidate_all()

        assert cache.data.linter == {}
        assert cache.data.formatter == {}


class TestRestoreDiagnostics:
    def test_restore_with_valid_rule(self, empty_config, tmp_path: Path):
        rule = MagicMock()
        rule.rule_id = "DOC01"
        rule.name = "missing-doc-keyword"
        rule.message = "Missing documentation"
        rule.get_severity_with_threshold.return_value = RuleSeverity.WARNING

        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {"DOC01": rule, "missing-doc-keyword": rule}

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(
                CachedDiagnostic(
                    rule_id="DOC01",
                    rule_name="missing-doc-keyword",
                    line=10,
                    col=1,
                    end_line=10,
                    end_col=5,
                    severity="W",
                    arguments=(),
                ),
            ),
        )

        source = tmp_path / "test.robot"
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)

        assert diagnostics is not None
        assert len(diagnostics) == 1
        assert diagnostics[0].rule == rule
        assert diagnostics[0].source.path == source

    def test_restore_returns_none_when_rule_missing(self, empty_config, tmp_path: Path):
        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {}  # No rules available

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(
                CachedDiagnostic(
                    rule_id="DOC01",
                    rule_name="missing-doc-keyword",
                    line=10,
                    col=1,
                    end_line=10,
                    end_col=5,
                    severity="W",
                    arguments=(),
                ),
            ),
        )

        source = tmp_path / "test.robot"
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)

        # Should return None because rule doesn't exist
        assert diagnostics is None

    def test_restore_with_arguments(self, empty_config, tmp_path: Path):
        rule = MagicMock()
        rule.rule_id = "LEN01"
        rule.name = "too-long-keyword"
        rule.message = "Keyword is too long"
        rule.get_severity_with_threshold.return_value = RuleSeverity.WARNING

        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {"LEN01": rule}

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(
                CachedDiagnostic(
                    rule_id="LEN01",
                    rule_name="too-long-keyword",
                    line=5,
                    col=0,
                    end_line=50,
                    end_col=0,
                    severity="W",
                    arguments=(("length", 45), ("max_length", 40)),
                ),
            ),
        )

        source = tmp_path / "test.robot"
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)

        assert diagnostics is not None
        assert len(diagnostics) == 1
        assert diagnostics[0].reported_arguments == {"length": 45, "max_length": 40}

    def test_restore_with_empty_diagnostics(self, empty_config, tmp_path: Path):
        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {"DOC01": MagicMock()}

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(),  # Empty
        )

        source = tmp_path / "test.robot"
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)

        assert diagnostics is not None
        assert len(diagnostics) == 0

    def test_restore_finds_rule_by_name(self, empty_config, tmp_path: Path):
        rule = MagicMock()
        rule.rule_id = "DOC01"
        rule.name = "missing-doc-keyword"
        rule.get_severity_with_threshold.return_value = RuleSeverity.WARNING

        # Only name in rules dict, not ID
        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {"missing-doc-keyword": rule}

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(
                CachedDiagnostic(
                    rule_id="DOC01",
                    rule_name="missing-doc-keyword",
                    line=10,
                    col=1,
                    end_line=10,
                    end_col=5,
                    severity="W",
                    arguments=(),
                ),
            ),
        )

        source = tmp_path / "test.robot"
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)

        assert diagnostics is not None
        assert len(diagnostics) == 1


class TestCachedDiagnosticFromDiagnostic:
    def test_from_diagnostic(self, empty_config, tmp_path: Path):
        rule = MagicMock()
        rule.rule_id = "DOC01"
        rule.name = "missing-doc-keyword"
        rule.message = "Missing documentation in '{name}'"
        rule.get_severity_with_threshold.return_value = RuleSeverity.WARNING

        source = SourceFile(path=tmp_path / "test.robot", config=empty_config)
        diagnostic = Diagnostic(
            rule=rule,
            source=source,
            lineno=10,
            col=1,
            end_lineno=10,
            end_col=20,
            name="My Keyword",
        )

        cached = CachedDiagnostic.from_diagnostic(diagnostic)

        assert cached.rule_id == "DOC01"
        assert cached.rule_name == "missing-doc-keyword"
        assert cached.line == 10
        assert cached.col == 1
        assert cached.end_line == 10
        assert cached.end_col == 20
        assert cached.severity == "W"
        assert dict(cached.arguments) == {"name": "My Keyword"}


class TestRobocopCacheEdgeCases:
    def test_set_linter_entry_with_deleted_file(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        # File doesn't exist - should handle gracefully

        cache.set_linter_entry(test_file, "hash", [])

        # Entry should not be added since file doesn't exist
        assert str(test_file.resolve()) not in cache.data.linter

    def test_set_formatter_entry_with_deleted_file(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        # File doesn't exist

        cache.set_formatter_entry(test_file, "hash", needs_formatting=False)

        # Entry should not be added
        assert str(test_file.resolve()) not in cache.data.formatter

    def test_get_linter_entry_file_deleted_after_cache(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_linter_entry(test_file, "hash123", [])

        # Delete the file
        test_file.unlink()

        # Entry should be invalidated since file no longer exists
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is None

    def test_get_formatter_entry_invalid_mtime(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_formatter_entry(test_file, "hash123", needs_formatting=False)

        # Modify the file
        test_file.write_text("new content")

        entry = cache.get_formatter_entry(test_file, "hash123")
        assert entry is None

    def test_get_formatter_entry_invalid_config_hash(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache.set_formatter_entry(test_file, "hash123", needs_formatting=False)

        entry = cache.get_formatter_entry(test_file, "different_hash")
        assert entry is None

    def test_get_formatter_entry_returns_none_when_disabled(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=False, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        entry = cache.get_formatter_entry(test_file, "hash")
        assert entry is None

    def test_save_does_nothing_when_not_dirty(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        # Access data to trigger load (creates empty cache)
        _ = cache.data

        # Don't add anything, just save
        cache.save()

        # Cache directory should not be created since nothing was modified
        assert not cache_dir.exists()

    def test_cache_persistence_across_instances(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        # First instance - add entry and save
        cache1 = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        cache1.set_linter_entry(test_file, "hash123", [])
        cache1.save()

        # Second instance - should load the saved data
        cache2 = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        entry = cache2.get_linter_entry(test_file, "hash123")

        assert entry is not None
        assert entry.config_hash == "hash123"

    def test_invalidate_all_then_save(self, tmp_path: Path):
        cache_dir = tmp_path / CACHE_DIR_NAME
        test_file = tmp_path / "test.robot"
        test_file.write_text("content")

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        cache.set_linter_entry(test_file, "hash", [])
        cache.set_formatter_entry(test_file, "hash", needs_formatting=True)
        cache.save()

        # Invalidate and save
        cache.invalidate_all()
        cache.save()

        # Load in new instance - should be empty
        cache2 = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        assert cache2.data.linter == {}
        assert cache2.data.formatter == {}

    def test_verbose_flag_stored(self, tmp_path: Path):
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=True)
        assert cache.verbose is True

        cache2 = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        assert cache2.verbose is False


class TestCacheConfigFromToml:
    def test_from_toml_disabled(self, tmp_path: Path):
        config = {"cache": False}
        cache_config = RawCacheConfig.from_dict(config, tmp_path)

        assert cache_config.enabled is False

    def test_from_toml_custom_dir_relative(self, tmp_path: Path):
        config = {"cache_dir": "custom_cache"}
        cache_config = RawCacheConfig.from_dict(config, tmp_path)

        assert cache_config.cache_dir == tmp_path / "custom_cache"

    def test_from_toml_custom_dir_absolute(self, tmp_path: Path):
        absolute_path = tmp_path / "absolute_cache"
        config = {"cache_dir": str(absolute_path)}
        cache_config = RawCacheConfig.from_dict(config, tmp_path)

        assert cache_config.cache_dir == absolute_path


class TestCacheEdgeCases:
    """Additional edge case tests for cache functionality."""

    def test_empty_file_cached_then_modified(self, tmp_path: Path):
        """Test that empty file is cached and invalidated when content added."""
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "empty.robot"
        test_file.write_text("", encoding="utf-8")

        # Cache empty file
        cache.set_linter_entry(test_file, "hash123", [])
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is not None
        assert entry.metadata.size == 0

        # Add content
        test_file.write_text("*** Test Cases ***\n", encoding="utf-8")

        # Cache should be invalidated
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is None

    def test_file_with_content_then_emptied(self, tmp_path: Path):
        """Test that file is invalidated when emptied."""
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Cache file with content
        cache.set_linter_entry(test_file, "hash123", [])
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is not None
        assert entry.metadata.size > 0

        # Empty the file
        test_file.write_text("", encoding="utf-8")

        # Cache should be invalidated
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is None

    def test_cache_save_failure_keeps_dirty_flag(self, tmp_path: Path, monkeypatch):
        """Test that if save fails, dirty flag remains True for retry."""
        cache_dir = tmp_path / "cache"
        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content", encoding="utf-8")

        # Add entry (sets dirty=True)
        cache.set_linter_entry(test_file, "hash", [])
        assert cache._dirty is True  # noqa: SLF001

        # Monkeypatch write_bytes to simulate write failure
        def mock_write_bytes(_self, _data):
            raise OSError("Permission denied")

        monkeypatch.setattr(Path, "write_bytes", mock_write_bytes)

        # Attempt save - should fail but not crash
        cache.save()
        # Dirty flag should remain True
        assert cache._dirty is True  # noqa: SLF001

    def test_relative_vs_absolute_path_consistency(self, tmp_path: Path):
        """Test that same file accessed via relative and absolute paths uses same cache entry."""
        cache = RobocopCache(cache_dir=tmp_path / "cache", enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("content", encoding="utf-8")

        # Cache using absolute path
        abs_path = test_file.resolve()
        cache.set_linter_entry(abs_path, "hash123", [])

        # Retrieve using relative path (from tmp_path)
        original_cwd = Path.cwd()
        try:
            os.chdir(tmp_path)
            rel_path = Path("test.robot")
            entry = cache.get_linter_entry(rel_path, "hash123")
            assert entry is not None, "Should find entry using relative path"
        finally:
            os.chdir(original_cwd)

    def test_cache_with_unicode_filename(self, tmp_path: Path):
        """Test cache handles unicode filenames correctly."""
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "tëst_файл_测试.robot"
        test_file.write_text("*** Test Cases ***\n", encoding="utf-8")

        # Should cache and retrieve successfully
        cache.set_linter_entry(test_file, "hash123", [])
        entry = cache.get_linter_entry(test_file, "hash123")
        assert entry is not None

        # Verify cache persistence
        cache.save()
        cache2 = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        entry2 = cache2.get_linter_entry(test_file, "hash123")
        assert entry2 is not None

    def test_formatter_entry_with_needs_formatting_true(self, tmp_path: Path):
        """Test formatter cache behavior when needs_formatting=True."""
        cache = RobocopCache(cache_dir=tmp_path, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\n", encoding="utf-8")

        # Cache with needs_formatting=True
        cache.set_formatter_entry(test_file, "hash123", needs_formatting=True)
        entry = cache.get_formatter_entry(test_file, "hash123")

        assert entry is not None
        assert entry.needs_formatting is True

        # Verify it's cached but formatter should still process it
        # (formatter logic skips only when needs_formatting=False)

    def test_multiple_diagnostics_one_rule_missing(self, empty_config, tmp_path: Path):
        """Test restore_diagnostics with multiple diagnostics where one rule is missing."""
        rule1 = MagicMock()
        rule1.rule_id = "DOC01"
        rule1.name = "missing-doc"

        # Only have rule1, not rule2
        resolved_config = MagicMock(spec=ResolvedConfig)
        resolved_config.rules = {"DOC01": rule1}

        cached_entry = LinterCacheEntry(
            metadata=FileMetadata(mtime=123.0, size=100),
            config_hash="hash",
            diagnostics=(
                CachedDiagnostic(
                    rule_id="DOC01",
                    rule_name="missing-doc",
                    line=10,
                    col=1,
                    end_line=10,
                    end_col=5,
                    severity="W",
                    arguments=(),
                ),
                CachedDiagnostic(
                    rule_id="DOC02",  # This rule doesn't exist
                    rule_name="missing-doc-keyword",
                    line=20,
                    col=1,
                    end_line=20,
                    end_col=5,
                    severity="W",
                    arguments=(),
                ),
            ),
        )

        source = tmp_path / "test.robot"
        # Should return None because one rule is missing (invalidates entire cache entry)
        diagnostics = restore_diagnostics(cached_entry, source, empty_config, resolved_config)
        assert diagnostics is None

    def test_cache_data_lazy_loading(self, tmp_path: Path):
        """Test that cache data is loaded lazily on first access."""
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache_dir.mkdir()
        cache_file = cache_dir / CACHE_FILE_NAME
        cache_file.write_bytes(
            msgpack.packb(
                {
                    "robocop_version": __version__,
                    "linter": {
                        "test": {
                            "mtime": 123,
                            "size": 1,
                            "config_hash": "x",
                            "diagnostics": [],
                        }
                    },
                    "formatter": {},
                },
                use_bin_type=True,
            )
        )

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)

        # Accessing .data triggers load
        data = cache.data
        assert data is not None
        assert "test" in data.linter

        # Second access should use cached data
        data2 = cache.data
        assert data2 is data  # Same object


class TestGitignoreCreation:
    """Test that .gitignore file is created in cache directory."""

    def test_gitignore_created_on_cache_save(self, tmp_path: Path):
        """Test that .gitignore file is created when cache is saved."""
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Add an entry to make cache dirty
        cache.set_linter_entry(test_file, "config_hash", [])
        cache.save()

        # Assert .gitignore was created
        gitignore_file = cache_dir / ".gitignore"
        assert gitignore_file.exists(), ".gitignore should be created in cache directory"
        assert gitignore_file.read_text(encoding="utf-8") == "*\n", ".gitignore should contain '*'"

    def test_gitignore_not_overwritten_if_exists(self, tmp_path: Path):
        """Test that existing .gitignore file is not overwritten."""
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache_dir.mkdir()
        gitignore_file = cache_dir / ".gitignore"

        # Create custom .gitignore with different content
        custom_content = "# Custom gitignore\ncache.msgpack\n"
        gitignore_file.write_text(custom_content, encoding="utf-8")

        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Save cache
        cache.set_linter_entry(test_file, "config_hash", [])
        cache.save()

        # Assert .gitignore was not overwritten
        assert gitignore_file.read_text(encoding="utf-8") == custom_content

    def test_gitignore_created_in_custom_cache_dir(self, tmp_path: Path):
        """Test that .gitignore is created in custom cache directory."""
        custom_cache_dir = tmp_path / "my_custom_cache"
        cache = RobocopCache(cache_dir=custom_cache_dir, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Save cache
        cache.set_linter_entry(test_file, "config_hash", [])
        cache.save()

        # Assert .gitignore was created in custom directory
        gitignore_file = custom_cache_dir / ".gitignore"
        assert gitignore_file.exists(), ".gitignore should be created in custom cache directory"
        assert gitignore_file.read_text(encoding="utf-8") == "*\n"

    def test_cache_works_if_gitignore_creation_fails(self, tmp_path: Path, monkeypatch):
        """Test that cache still works if .gitignore creation fails."""
        cache_dir = tmp_path / CACHE_DIR_NAME
        cache = RobocopCache(cache_dir=cache_dir, enabled=True, verbose=False)
        test_file = tmp_path / "test.robot"
        test_file.write_text("*** Test Cases ***\nTest\n    Log    Hello\n", encoding="utf-8")

        # Mock write_text to raise OSError
        original_write_text = Path.write_text

        def mock_write_text(self, *args, **kwargs):
            if self.name == ".gitignore":
                raise OSError("Permission denied")
            return original_write_text(self, *args, **kwargs)

        monkeypatch.setattr(Path, "write_text", mock_write_text)

        # Save cache - should not raise even though .gitignore creation fails
        cache.set_linter_entry(test_file, "config_hash", [])
        cache.save()

        # Cache should still be saved
        cache_file = cache_dir / CACHE_FILE_NAME
        assert cache_file.exists(), "Cache should be saved even if .gitignore creation fails"
