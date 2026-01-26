"""
File-level caching for Robocop linter and formatter.

This module provides caching infrastructure to skip processing unchanged files,
significantly improving performance on subsequent runs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msgpack

from robocop import __version__
from robocop.source_file import SourceFile

if TYPE_CHECKING:
    from robocop.config import Config
    from robocop.linter.diagnostics import Diagnostic


CACHE_VERSION = "1.0"
CACHE_DIR_NAME = ".robocop_cache"
CACHE_FILE_NAME = "cache.msgpack"


@dataclass(frozen=True)
class FileMetadata:
    """Immutable file metadata used for cache invalidation."""

    mtime: float
    size: int

    @classmethod
    def from_path(cls, path: Path) -> FileMetadata:
        """
        Create metadata from a file path.

        Returns:
            FileMetadata: The metadata of the file.

        """
        stat = path.stat()
        return cls(mtime=stat.st_mtime, size=stat.st_size)


@dataclass(frozen=True)
class CachedDiagnostic:
    """Immutable serialized diagnostic for cache storage."""

    rule_id: str
    rule_name: str
    line: int
    col: int
    end_line: int
    end_col: int
    severity: str
    arguments: tuple[tuple[str, Any], ...]

    @classmethod
    def from_diagnostic(cls, diagnostic: Diagnostic) -> CachedDiagnostic:
        """
        Create cached diagnostic from a Diagnostic object.

        Returns:
            CachedDiagnostic: The cached diagnostic object.

        """
        return cls(
            rule_id=diagnostic.rule.rule_id,
            rule_name=diagnostic.rule.name,
            line=diagnostic.range.start.line,
            col=diagnostic.range.start.character,
            end_line=diagnostic.range.end.line,
            end_col=diagnostic.range.end.character,
            severity=diagnostic.severity.value,
            arguments=tuple(sorted(diagnostic.reported_arguments.items())),
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the cached diagnostic.

        """
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "line": self.line,
            "col": self.col,
            "end_line": self.end_line,
            "end_col": self.end_col,
            "severity": self.severity,
            "arguments": dict(self.arguments),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CachedDiagnostic:
        """
        Create from dictionary loaded from cache.

        Returns:
            CachedDiagnostic: The cached diagnostic object.

        """
        return cls(
            rule_id=data["rule_id"],
            rule_name=data["rule_name"],
            line=data["line"],
            col=data["col"],
            end_line=data["end_line"],
            end_col=data["end_col"],
            severity=data["severity"],
            arguments=tuple(sorted(data.get("arguments", {}).items())),
        )


@dataclass(frozen=True)
class LinterCacheEntry:
    """Immutable cache entry for linter results."""

    metadata: FileMetadata
    config_hash: str
    diagnostics: tuple[CachedDiagnostic, ...]

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the linter cache entry.

        """
        return {
            "mtime": self.metadata.mtime,
            "size": self.metadata.size,
            "config_hash": self.config_hash,
            "diagnostics": [d.to_dict() for d in self.diagnostics],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LinterCacheEntry:
        """
        Create from dictionary loaded from cache.

        Returns:
            LinterCacheEntry: The linter cache entry object.

        """
        return cls(
            metadata=FileMetadata(mtime=data["mtime"], size=data["size"]),
            config_hash=data["config_hash"],
            diagnostics=tuple(CachedDiagnostic.from_dict(d) for d in data.get("diagnostics", [])),
        )


@dataclass(frozen=True)
class FormatterCacheEntry:
    """Immutable cache entry for formatter results."""

    metadata: FileMetadata
    config_hash: str
    needs_formatting: bool

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the formatter cache entry.

        """
        return {
            "mtime": self.metadata.mtime,
            "size": self.metadata.size,
            "config_hash": self.config_hash,
            "needs_formatting": self.needs_formatting,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> FormatterCacheEntry:
        """
        Create from dictionary loaded from cache.

        Returns:
            FormatterCacheEntry: The formatter cache entry object.

        """
        return cls(
            metadata=FileMetadata(mtime=data["mtime"], size=data["size"]),
            config_hash=data["config_hash"],
            needs_formatting=data.get("needs_formatting", True),
        )


@dataclass
class CacheData:
    """Mutable container for cache data."""

    version: str = CACHE_VERSION
    robocop_version: str = field(default_factory=lambda: __version__)
    linter: dict[str, LinterCacheEntry] = field(default_factory=dict)
    formatter: dict[str, FormatterCacheEntry] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation of the cache data.

        """
        return {
            "version": self.version,
            "robocop_version": self.robocop_version,
            "linter": {path: entry.to_dict() for path, entry in self.linter.items()},
            "formatter": {path: entry.to_dict() for path, entry in self.formatter.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CacheData:
        """
        Create from dictionary loaded from cache.

        Returns:
            CacheData: The cache data object.

        """
        return cls(
            version=data.get("version", CACHE_VERSION),
            robocop_version=data.get("robocop_version", ""),
            linter={path: LinterCacheEntry.from_dict(entry) for path, entry in data.get("linter", {}).items()},
            formatter={path: FormatterCacheEntry.from_dict(entry) for path, entry in data.get("formatter", {}).items()},
        )


class RobocopCache:
    """
    Manages file-level caching for linter and formatter.

    The cache stores results keyed by absolute file path, with metadata
    for invalidation (mtime, size, config hash).
    """

    def __init__(
        self,
        cache_dir: Path | None = None,
        enabled: bool = True,
        verbose: bool = False,
    ) -> None:
        """
        Initialize the cache.

        Args:
            cache_dir: Custom cache directory. Defaults to .robocop_cache in cwd.
            enabled: Whether caching is enabled.
            verbose: Whether to print verbose messages (e.g., on errors).

        """
        self.enabled = enabled
        self.cache_dir = cache_dir or Path.cwd() / CACHE_DIR_NAME
        self.verbose = verbose
        self._data: CacheData | None = None
        self._dirty = False
        self._path_cache: dict[Path, str] = {}  # Instance-bound path normalization cache

    @property
    def data(self) -> CacheData:
        """Get cache data, loading from disk if needed."""
        if self._data is None:
            self._load()
        return self._data

    def _load(self) -> None:
        """Load cache from disk."""
        # Handle missing cache directory (first run)
        if not self.cache_dir.exists():
            self._data = CacheData()
            return

        cache_file = self.cache_dir / CACHE_FILE_NAME

        if not cache_file.is_file():
            self._data = CacheData()
            return

        try:
            raw_data = msgpack.unpackb(cache_file.read_bytes(), raw=False, strict_map_key=False)

            # Invalidate if version changed
            if raw_data.get("robocop_version") != __version__:
                self._data = CacheData()
                return

            self._data = CacheData.from_dict(raw_data)
        except (
            msgpack.exceptions.UnpackException,
            msgpack.exceptions.ExtraData,
            KeyError,
            TypeError,
            OSError,
        ):
            # Corrupted cache - start fresh
            self._data = CacheData()

    def save(self) -> None:
        """Save cache to disk if modified."""
        should_skip = not self.enabled or not self._dirty or self._data is None
        if should_skip:
            return

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._create_gitignore()
        cache_file = self.cache_dir / CACHE_FILE_NAME

        try:
            cache_file.write_bytes(msgpack.packb(self._data.to_dict(), use_bin_type=True))
            self._dirty = False
        except OSError as err:
            if self.verbose:
                print(f"Warning: Failed to save cache to {cache_file}: {err}")

    def _create_gitignore(self) -> None:
        """Create .gitignore file in cache directory to prevent committing cache files."""
        gitignore_file = self.cache_dir / ".gitignore"
        if not gitignore_file.exists():
            try:
                gitignore_file.write_text("*\n", encoding="utf-8")
            except OSError:
                # Silently ignore if we can't create .gitignore
                pass

    def invalidate_all(self) -> None:
        """Clear the entire cache."""
        self._data = CacheData()
        self._dirty = True

    def _normalize_path(self, path: Path) -> str:
        """
        Normalize path to string for consistent cache keys.

        Uses instance-bound cache to avoid repeated filesystem I/O from path.resolve().
        The cache is cleared when the RobocopCache instance is garbage collected,
        preventing memory leaks in long-running processes.

        Returns:
            Normalized absolute path as string.

        """
        if path not in self._path_cache:
            self._path_cache[path] = str(path.resolve())
        return self._path_cache[path]

    @staticmethod
    def _is_entry_valid(
        path: Path,
        entry_metadata: FileMetadata,
        config_hash: str,
        entry_config_hash: str,
    ) -> bool:
        """
        Check if a cache entry is still valid.

        Returns:
            True if the cache entry is valid, False otherwise.

        """
        # Check the cheapest condition first (string comparison)
        if config_hash != entry_config_hash:
            return False

        # Then check file metadata (requires I/O)
        try:
            current_metadata = FileMetadata.from_path(path)
        except OSError:
            return False

        return current_metadata.mtime == entry_metadata.mtime and current_metadata.size == entry_metadata.size

    # Generic cache entry methods

    def _get_entry(
        self,
        cache_dict: dict[str, LinterCacheEntry] | dict[str, FormatterCacheEntry],
        path: Path,
        config_hash: str,
    ) -> LinterCacheEntry | FormatterCacheEntry | None:
        """
        Retrieve and validate a cache entry.

        Args:
            cache_dict: Dictionary containing cache entries (linter or formatter).
            path: Absolute path to the file.
            config_hash: Hash of the current configuration.

        Returns:
            Cached entry if valid, None otherwise.

        """
        if not self.enabled:
            return None

        str_path = self._normalize_path(path)
        entry = cache_dict.get(str_path)

        if entry is None:
            return None

        if not self._is_entry_valid(path, entry.metadata, config_hash, entry.config_hash):
            # Invalidate stale entry
            del cache_dict[str_path]
            self._dirty = True
            return None

        return entry

    # Linter cache methods

    def get_linter_entry(self, path: Path, config_hash: str) -> LinterCacheEntry | None:
        """
        Get cached linter entry if valid.

        Args:
            path: Absolute path to the file.
            config_hash: Hash of current linter configuration.

        Returns:
            Cached entry if valid, None otherwise.

        """
        return self._get_entry(self.data.linter, path, config_hash)  # type: ignore[return-value]

    def set_linter_entry(
        self,
        path: Path,
        config_hash: str,
        diagnostics: list[Diagnostic],
    ) -> None:
        """
        Store linter results in cache.

        Args:
            path: Absolute path to the file.
            config_hash: Hash of linter configuration used.
            diagnostics: List of diagnostics found.

        """
        if not self.enabled:
            return
        try:
            metadata = FileMetadata.from_path(path)
        except OSError:
            return

        entry = LinterCacheEntry(
            metadata=metadata,
            config_hash=config_hash,
            diagnostics=tuple(CachedDiagnostic.from_diagnostic(d) for d in diagnostics),
        )
        str_path = self._normalize_path(path)
        self.data.linter[str_path] = entry
        self._dirty = True

    # Formatter cache methods

    def get_formatter_entry(self, path: Path, config_hash: str) -> FormatterCacheEntry | None:
        """
        Get cached formatter entry if valid.

        Args:
            path: Absolute path to the file.
            config_hash: Hash of current formatter configuration.

        Returns:
            Cached entry if valid, None otherwise.

        """
        return self._get_entry(self.data.formatter, path, config_hash)  # type: ignore[return-value]

    def set_formatter_entry(
        self,
        path: Path,
        config_hash: str,
        needs_formatting: bool,
    ) -> None:
        """
        Store formatter results in cache.

        Args:
            path: Absolute path to the file.
            config_hash: Hash of formatter configuration used.
            needs_formatting: Whether the file needed formatting.

        """
        if not self.enabled:
            return
        try:
            metadata = FileMetadata.from_path(path)
        except OSError:
            return

        entry = FormatterCacheEntry(
            metadata=metadata,
            config_hash=config_hash,
            needs_formatting=needs_formatting,
        )
        str_path = self._normalize_path(path)
        self.data.formatter[str_path] = entry
        self._dirty = True


def restore_diagnostics(
    cached_entry: LinterCacheEntry,
    source: Path,
    config: Config,
) -> list[Diagnostic] | None:
    """
    Restore Diagnostic objects from cached data.

    Args:
        cached_entry: The cached linter entry.
        source: The source file path (Path object for consistency with normal diagnostics).
        config: Configuration associated with the source file.

    Returns:
        List of restored diagnostics, or None if restoration failed
        (e.g. rule no longer exists).

    """
    from robocop.linter.diagnostics import Diagnostic  # noqa: PLC0415

    restored = []
    for cached_diag in cached_entry.diagnostics:
        # Try to find rule by ID first, fall back to name
        rule = config.linter.rules.get(cached_diag.rule_id)
        if rule is None:
            rule = config.linter.rules.get(cached_diag.rule_name)

        if rule is None:
            # Rule no longer exists - invalidate cache entry
            return None

        diagnostic = Diagnostic(
            rule=rule,
            source=SourceFile(source, config),
            lineno=cached_diag.line,
            col=cached_diag.col,
            end_lineno=cached_diag.end_line,
            end_col=cached_diag.end_col,
            **dict(cached_diag.arguments),
        )
        restored.append(diagnostic)

    return restored
