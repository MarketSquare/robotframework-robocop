"""
Importing Robot Framework libraries to find out what keywords they provide.

Unlike the rest of the project analysis, which is based purely on the abstract syntax tree, loading a library
**executes the library code**. That is why it only happens when project level rules are enabled and can be disabled
with the ``--no-analyze-libraries`` option.

By default libraries are imported synchronously, in the Robocop process itself. With the ``--library-workers``
option every library is instead imported in a separate process, several of them at the same time. Separate
processes are slower to start, but they can be killed on timeout and they keep the imported code out of the
Robocop process.

Libraries that fail to import are not reported as an internal error. Such library simply provides no keywords, so
rules using this information stay silent instead of reporting false positives.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from fnmatch import fnmatch
from functools import cache
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING, Any

from robocop.linter.utils.misc import normalize_robot_name
from robocop.project.definitions import ArgumentsSpec, KeywordDefinition, Location, embedded_name_pattern

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robocop.cache import RobocopCache
    from robocop.project.definitions import ResolvedImport

WORKER_MODULE = "robocop.project._libdoc_worker"
DEFAULT_TIMEOUT = 10
DEFAULT_LIBRARY_WORKERS = False
MAX_WORKERS = 8


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
        embedded=embedded_name_pattern(name),
        library_name=library_name,
    )


@dataclass
class LibraryLoader:
    """
    Imports libraries and caches the results.

    Every library is imported only once, even if it is used in several files. Libraries imported with different
    arguments are treated as different libraries, since the arguments may change the provided keywords.

    By default libraries are imported synchronously, in the Robocop process. With ``workers`` enabled every library
    is imported in a separate process instead and libraries are imported in parallel. Only such imports can be
    stopped with the timeout, since a library imported in the Robocop process cannot be safely interrupted.

    Successful imports are also stored in the persistent Robocop cache, so that the library does not have to be
    imported again in the next run. Cached results are only used for libraries installed outside of the analyzed
    project and are invalidated when the library source file, the Python interpreter or the Robot Framework
    version changes.
    """

    search_paths: list[Path] = field(default_factory=list)
    timeout: int = DEFAULT_TIMEOUT
    ignored_libraries: list[str] = field(default_factory=list)
    cache: RobocopCache | None = None
    project_root: Path | None = None
    workers: bool = DEFAULT_LIBRARY_WORKERS
    _cache: dict[tuple[str, tuple[str, ...]], LibrarySpec] = field(default_factory=dict, init=False)
    _scheduled: list[LibraryRequest] = field(default_factory=list, init=False)

    def load(self, request: LibraryRequest) -> LibrarySpec:
        """
        Import the library and return its keywords, using the cached result if it is already imported.

        Returns:
            LibrarySpec with the library keywords, or with the error if it could not be imported.

        """
        cached = self._cache.get(request.cache_key)
        if cached is None:
            self._preload_scheduled()
            cached = self._cache.get(request.cache_key)
        if cached is None:
            cached = self._load(request)
            self._cache[request.cache_key] = cached
        return self._with_name(cached, request.alias or cached.name)

    def schedule_preload(self, requests: Iterable[LibraryRequest]) -> None:
        """
        Remember libraries used in the project, so that they can be imported in parallel.

        Nothing is imported here. The libraries are imported together, in parallel, when the first library is
        needed. With the default, synchronous loading this method does nothing and every library is imported
        separately when it is used for the first time.
        """
        if not self.workers:
            return
        self._scheduled.extend(requests)

    def _preload_scheduled(self) -> None:
        """Import all scheduled libraries at once, using a pool of worker processes."""
        if not self._scheduled:
            return
        pending: dict[tuple[str, tuple[str, ...]], LibraryRequest] = {}
        for request in self._scheduled:
            if request.cache_key not in self._cache and request.cache_key not in pending:
                pending[request.cache_key] = request
        self._scheduled = []
        if len(pending) < 2:  # a single library does not benefit from the worker pool
            return
        with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(pending))) as executor:
            specs = executor.map(self._load, pending.values())
            for cache_key, spec in zip(pending, specs, strict=False):
                self._cache.setdefault(cache_key, spec)

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
        Import the library and read its keywords.

        Returns:
            LibrarySpec with the library keywords, or with the error if it could not be imported.

        """
        if self.is_ignored(request.name):
            return LibrarySpec(name=request.name, error="Library is excluded from the analysis")
        response = self._import_library(request)
        if response.get("status") != "ok":
            return LibrarySpec(name=request.name, error=response.get("error", "Unknown error"))
        name = response.get("name") or request.name
        fallback_source = request.source or Path(request.name)
        keywords = tuple(
            _keyword_definition(keyword, name, fallback_source) for keyword in response.get("keywords", [])
        )
        return LibrarySpec(name=name, keywords=keywords)

    def _import_library(self, request: LibraryRequest) -> dict[str, Any]:
        """
        Import the library, reusing the result stored in the persistent cache when it is still valid.

        Returns:
            Response describing the library keywords or the failure.

        """
        cache_key = _persistent_cache_key(request)
        if self.cache is not None:
            cached = self.cache.get_library_entry(cache_key, environment_hash())
            if cached is not None:
                return cached
        response = self._run_worker(request) if self.workers else self._import_in_process(request)
        if self.cache is not None and response.get("status") == "ok":
            source = response.get("source")
            if source and self._can_be_cached(Path(source)):
                self.cache.set_library_entry(cache_key, environment_hash(), Path(source), response)
        return response

    def _can_be_cached(self, source: Path) -> bool:
        """
        Check if the imported library can be stored in the persistent cache.

        Libraries that are a part of the analyzed project are not cached, since they change together with the
        rest of the sources and a change in any of their modules would not be detected.

        Returns:
            True if the library can be stored between the runs.

        """
        if not source.is_file():
            return False
        if self.project_root is None:
            return True
        return self.project_root.resolve() not in source.resolve().parents

    def _worker_request(self, request: LibraryRequest) -> dict[str, Any]:
        """
        Build the request describing the library import.

        Returns:
            Request understood by the library import worker.

        """
        return {
            "name": str(request.source) if request.source else request.name,
            "args": list(request.args),
            "search_paths": [str(path) for path in self.search_paths],
        }

    def _import_in_process(self, request: LibraryRequest) -> dict[str, Any]:
        """
        Import the library in the Robocop process.

        This is the default way of importing libraries, since starting a process for every library is slow.
        Anything the library or Robot Framework prints during the import is discarded, so that it does not
        corrupt the Robocop output. The import cannot be stopped, so the timeout does not apply here.

        Returns:
            Response describing the library keywords or the failure.

        """
        from robocop.project._libdoc_worker import load_library  # noqa: PLC0415

        already_imported = set(sys.modules)
        try:
            return load_library(self._worker_request(request))
        finally:
            self._forget_local_modules(already_imported, request)

    def _forget_local_modules(self, already_imported: set[str], request: LibraryRequest) -> None:
        """
        Remove modules imported from the project and the search paths from ``sys.modules``.

        Libraries installed in the environment are left imported, since they do not change while Robocop runs.
        Libraries coming from the analyzed project may be modified between the runs, which matters when Robocop
        is used from a long living process such as the MCP server, and different libraries may even share the
        module name. Such modules are removed, so that they are read from the disk again next time.
        """
        local_paths = [
            path.resolve()
            for path in (*self.search_paths, self.project_root, request.source.parent if request.source else None)
            if path is not None
        ]
        if not local_paths:
            return
        for name in set(sys.modules) - already_imported:
            module = sys.modules.get(name)
            source = getattr(module, "__file__", None)
            if not source:
                continue
            parents = Path(source).resolve().parents
            if any(local_path in parents for local_path in local_paths):
                sys.modules.pop(name, None)

    def _run_worker(self, request: LibraryRequest) -> dict[str, Any]:
        """
        Run the worker process importing the library.

        Returns:
            Response from the worker, or an error description if the worker failed or timed out.

        """
        with tempfile.TemporaryDirectory(prefix="robocop_libdoc_") as directory:
            output = Path(directory) / "response.json"
            payload = json.dumps({**self._worker_request(request), "output": str(output)})
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


def _persistent_cache_key(request: LibraryRequest) -> str:
    """
    Build the key identifying the library import in the persistent cache.

    Returns:
        Key built from the library name or path and its arguments.

    """
    name = str(request.source) if request.source else request.name
    return "::".join([name, *request.args])


@cache
def environment_hash() -> str:
    """
    Describe the environment the libraries are imported in.

    Libraries imported with a different Python interpreter or a different Robot Framework version may provide
    different keywords, so the cached results cannot be reused.

    Returns:
        Hash of the Python interpreter and the Robot Framework version.

    """
    from robot.version import VERSION as RF_VERSION  # noqa: PLC0415

    return sha256(f"{sys.executable}|{sys.version}|{RF_VERSION}".encode()).hexdigest()


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
    cache: RobocopCache | None = None,
    project_root: Path | None = None,
    workers: bool = DEFAULT_LIBRARY_WORKERS,
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
        cache=cache,
        project_root=project_root,
        workers=workers,
    )
