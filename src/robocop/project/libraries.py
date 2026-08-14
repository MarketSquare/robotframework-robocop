"""
Importing Robot Framework libraries to find out what keywords they provide.

Unlike the rest of the project analysis, which is based purely on the abstract syntax tree, loading a library
**executes the library code**. That is why it only happens in the opt-in ``check-project`` command, always in a
separate process with a timeout, and can be disabled with the ``--no-analyze-libraries`` option.

Libraries that fail to import are not reported as an internal error. Such library simply provides no keywords, so
rules using this information stay silent instead of reporting false positives.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import TYPE_CHECKING, Any

from robocop.linter.utils.misc import normalize_robot_name
from robocop.project.definitions import ArgumentsSpec, KeywordDefinition, Location, parse_embedded_arguments

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robocop.project.definitions import ResolvedImport

WORKER_MODULE = "robocop.project._libdoc_worker"
DEFAULT_TIMEOUT = 10


def worker_environment() -> dict[str, str]:
    """
    Build environment variables for the process importing the library.

    The current environment is passed to the worker, so that libraries can be configured with environment variables.
    On Windows ``SystemRoot`` is restored if it is missing, since without it the standard library cannot import
    modules using sockets.

    Returns:
        Environment variables for the worker process.

    """
    env = dict(os.environ)
    if sys.platform == "win32" and not any(name.upper() == "SYSTEMROOT" for name in env):
        windows_directory = _windows_directory()
        if windows_directory:
            env["SystemRoot"] = windows_directory
    return env


def _windows_directory() -> str | None:
    """
    Read the Windows directory without relying on the environment variables.

    Returns:
        Path to the Windows directory, or None if it could not be read.

    """
    import ctypes  # noqa: PLC0415

    buffer = ctypes.create_unicode_buffer(260)
    try:
        length = ctypes.windll.kernel32.GetWindowsDirectoryW(buffer, len(buffer))
    except (AttributeError, OSError):  # pragma: no cover - defensive, not available outside Windows
        return None
    return buffer.value if length else None


@dataclass(frozen=True)
class LibrarySpec:
    """Keywords provided by a single library import."""

    name: str
    keywords: tuple[KeywordDefinition, ...] = ()
    error: str | None = None

    @property
    def loaded(self) -> bool:
        """Whether the library was imported successfully."""
        return self.error is None


@dataclass(frozen=True)
class LibraryRequest:
    """Library import reduced to what is needed to import it."""

    name: str
    args: tuple[str, ...] = ()
    source: Path | None = None
    alias: str | None = None

    @property
    def cache_key(self) -> tuple[str, tuple[str, ...]]:
        """Key identifying the imported library, ignoring the alias it was imported with."""
        return (str(self.source) if self.source else self.name, self.args)

    @property
    def displayed_name(self) -> str:
        """Name used to refer to the library keywords."""
        return self.alias or self.name


def _keyword_definition(data: dict[str, Any], library_name: str, fallback_source: Path) -> KeywordDefinition:
    """
    Build keyword definition from the data returned by the worker process.

    Returns:
        KeywordDefinition describing a single library keyword.

    """
    name = data["name"]
    arguments = data.get("arguments") or {}
    source = Path(data["source"]) if data.get("source") else fallback_source
    lineno = data.get("lineno") or 0
    return KeywordDefinition(
        name=name,
        normalized_name=normalize_robot_name(name),
        location=Location(source=source, lineno=lineno, col=1, end_lineno=lineno, end_col=1),
        arguments=ArgumentsSpec(
            positional=tuple(arguments.get("positional", ())),
            defaults=frozenset(arguments.get("defaults", ())),
            var_positional=arguments.get("var_positional"),
            var_named=arguments.get("var_named"),
            named_only=tuple(arguments.get("named_only", ())),
        ),
        embedded=parse_embedded_arguments(name),
        library_name=library_name,
    )


@dataclass
class LibraryLoader:
    """
    Imports libraries in a separate process and caches the results.

    Every library is imported only once, even if it is used in several files. Libraries imported with different
    arguments are treated as different libraries, since the arguments may change the provided keywords.
    """

    search_paths: list[Path] = field(default_factory=list)
    timeout: int = DEFAULT_TIMEOUT
    ignored_libraries: list[str] = field(default_factory=list)
    _cache: dict[tuple[str, tuple[str, ...]], LibrarySpec] = field(default_factory=dict, init=False)

    def load(self, request: LibraryRequest) -> LibrarySpec:
        """
        Import the library and return its keywords, using the cached result if it is already imported.

        Returns:
            LibrarySpec with the library keywords, or with the error if it could not be imported.

        """
        cached = self._cache.get(request.cache_key)
        if cached is not None:
            return self._with_name(cached, request.displayed_name)
        spec = self._load(request)
        self._cache[request.cache_key] = spec
        return self._with_name(spec, request.displayed_name)

    def load_import(self, resolved: ResolvedImport) -> LibrarySpec | None:
        """
        Import the library described by the resolved ``Library`` import.

        Returns:
            LibrarySpec, or None if the library should not be imported at all.

        """
        if not resolved.args_resolved:
            return None
        return self.load(
            LibraryRequest(
                name=resolved.resolved_name,
                args=resolved.args,
                source=resolved.path,
                alias=resolved.alias,
            )
        )

    def is_ignored(self, name: str) -> bool:
        """
        Check if the library is excluded from the analysis with the ``ignored-libraries`` option.

        Returns:
            True if the library should not be imported.

        """
        return any(fnmatch(name, pattern) for pattern in self.ignored_libraries)

    @staticmethod
    def _with_name(spec: LibrarySpec, name: str) -> LibrarySpec:
        """
        Return the specification under the name used in the import.

        The same library can be imported with different aliases, but it is only imported once.

        Returns:
            LibrarySpec using the requested name.

        """
        if spec.name == name:
            return spec
        keywords = tuple(replace_library_name(keyword, name) for keyword in spec.keywords)
        return LibrarySpec(name=name, keywords=keywords, error=spec.error)

    def _load(self, request: LibraryRequest) -> LibrarySpec:
        """
        Import the library in a separate process.

        Returns:
            LibrarySpec with the library keywords, or with the error if it could not be imported.

        """
        if self.is_ignored(request.name):
            return LibrarySpec(name=request.name, error="Library is excluded from the analysis")
        response = self._run_worker(request)
        if response.get("status") != "ok":
            return LibrarySpec(name=request.name, error=response.get("error", "Unknown error"))
        fallback_source = request.source or Path(request.name)
        keywords = tuple(
            _keyword_definition(keyword, request.name, fallback_source) for keyword in response.get("keywords", [])
        )
        return LibrarySpec(name=request.name, keywords=keywords)

    def _run_worker(self, request: LibraryRequest) -> dict[str, Any]:
        """
        Run the worker process importing the library.

        Returns:
            Response from the worker, or an error description if the worker failed or timed out.

        """
        name = str(request.source) if request.source else request.name
        with tempfile.TemporaryDirectory(prefix="robocop_libdoc_") as directory:
            output = Path(directory) / "response.json"
            payload = json.dumps(
                {
                    "name": name,
                    "args": list(request.args),
                    "search_paths": [str(path) for path in self.search_paths],
                    "output": str(output),
                }
            )
            try:
                subprocess.run(  # noqa: S603
                    [sys.executable, "-m", WORKER_MODULE],
                    input=payload,
                    capture_output=True,
                    text=True,
                    env=worker_environment(),
                    timeout=self.timeout,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                return {"status": "error", "error": f"Importing the library timed out after {self.timeout}s"}
            except OSError as error:  # pragma: no cover - defensive, failure to start the process
                return {"status": "error", "error": f"Failed to start the library import process: {error}"}
            if not output.is_file():
                return {"status": "error", "error": "Library import process did not return any data"}
            try:
                response: dict[str, Any] = json.loads(output.read_text(encoding="utf-8"))
            except (OSError, ValueError) as error:  # pragma: no cover - defensive, corrupted response
                return {"status": "error", "error": f"Invalid response from the library import process: {error}"}
            return response


def replace_library_name(keyword: KeywordDefinition, library_name: str) -> KeywordDefinition:
    """
    Return a copy of the keyword that belongs to a library imported under a different name.

    Returns:
        KeywordDefinition with the updated library name.

    """
    return KeywordDefinition(
        name=keyword.name,
        normalized_name=keyword.normalized_name,
        location=keyword.location,
        arguments=keyword.arguments,
        embedded=keyword.embedded,
        library_name=library_name,
    )


def build_library_loader(
    search_paths: Iterable[Path] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    ignored_libraries: Iterable[str] | None = None,
) -> LibraryLoader:
    """
    Create the loader used to import libraries during the project analysis.

    Returns:
        Configured LibraryLoader.

    """
    return LibraryLoader(
        search_paths=list(search_paths or []),
        timeout=timeout,
        ignored_libraries=list(ignored_libraries or []),
    )
