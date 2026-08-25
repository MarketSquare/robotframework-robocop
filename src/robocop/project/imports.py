"""
Resolving ``Library``, ``Resource`` and ``Variables`` imports to paths on the disk.

Variables inside the import name are resolved using Robot Framework's own variable machinery, so escaping, nested
variables and environment variables (``%{VAR}`` and ``%{VAR=default}``) behave exactly like during the execution.

Imports that are not found next to the importing file are searched for in the search paths configured with the
``--pythonpath`` option, the same way Robot Framework searches for them during the execution.
"""

from __future__ import annotations

from glob import glob
from pathlib import Path
from typing import TYPE_CHECKING, Any

from robot.errors import DataError
from robot.libraries import STDLIBS
from robot.variables.search import contains_variable

from robocop.project.definitions import ImportStatus, ImportType, ResolvedImport

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robocop.project.definitions import Location
    from robocop.project.variables import VariableScope

LIBRARY_FILE_SUFFIXES = (".py", ".class", ".java")


def build_search_paths(entries: Iterable[str], root: Path) -> list[Path]:
    """
    Build the list of directories used to search for imports.

    Relative entries are resolved against the project root, matching the behaviour of other tools analysing
    Robot Framework projects. Glob patterns are supported, so ``libs/*`` adds every directory inside ``libs``.

    Returns:
        List of existing directories, in the order they should be searched.

    """
    search_paths: list[Path] = []
    seen: set[Path] = set()
    for entry in entries:
        pattern = Path(entry)
        absolute = pattern if pattern.is_absolute() else root / pattern
        for found in sorted(glob(str(absolute))):
            path = Path(found)
            if not path.is_dir():
                continue
            resolved = path.resolve()
            if resolved not in seen:
                seen.add(resolved)
                search_paths.append(resolved)
    return search_paths


class ImportResolver:
    """Resolves import names to paths, using variables visible in the importing file."""

    def __init__(self, scope: VariableScope, search_paths: list[Path] | None = None) -> None:
        self.scope = scope
        self.search_paths = search_paths if search_paths is not None else []

    def replace_variables(self, name: str) -> str | None:
        """
        Replace variables in the import name.

        Returns:
            Import name with variables replaced, or None if any variable could not be resolved.

        """
        if not contains_variable(name, "$@&%"):
            return name
        try:
            replaced = self.scope.as_robot_variables().replace_string(name, ignore_errors=False)
        except DataError:
            return None
        return str(replaced)

    def resolve(
        self,
        import_type: ImportType,
        name: str,
        location: Location,
        base_dir: Path,
        args: tuple[str, ...] = (),
        alias: str | None = None,
    ) -> ResolvedImport:
        """
        Resolve a single import.

        Args:
            import_type: Type of the import.
            name: Import name as written in the source code.
            location: Position of the import in the source file.
            base_dir: Directory of the file containing the import.
            args: Arguments of the ``Library`` or ``Variables`` import.
            alias: Name the library was imported with (``AS`` / ``WITH NAME``).

        Returns:
            ResolvedImport describing the outcome.

        """
        resolved_args, args_resolved = self._resolve_args(args)
        common: dict[str, Any] = {
            "import_type": import_type,
            "name": name,
            "location": location,
            "args": resolved_args,
            "alias": alias,
            "args_resolved": args_resolved,
        }
        resolved_name = self.replace_variables(name)
        if resolved_name is None:
            return ResolvedImport(
                **common,
                resolved_name=name,
                status=ImportStatus.UNRESOLVABLE,
                error="Import name contains variables that cannot be resolved statically",
            )
        if import_type == ImportType.LIBRARY and self._is_module_library(resolved_name):
            path = self._find_module_library(resolved_name)
            if path is None:
                return ResolvedImport(**common, resolved_name=resolved_name, status=ImportStatus.EXTERNAL)
            return ResolvedImport(**common, resolved_name=resolved_name, status=ImportStatus.RESOLVED, path=path)
        path = self._find_path(resolved_name, base_dir)
        if path is None:
            return ResolvedImport(**common, resolved_name=resolved_name, status=ImportStatus.NOT_FOUND)
        return ResolvedImport(**common, resolved_name=resolved_name, status=ImportStatus.RESOLVED, path=path)

    def _resolve_args(self, args: tuple[str, ...]) -> tuple[tuple[str, ...], bool]:
        """
        Replace variables in the import arguments.

        Import arguments may change the keywords provided by the library, so they need to be known before importing
        it. Arguments that cannot be resolved are kept as they are and reported with the second return value.

        Returns:
            Tuple with the resolved arguments and a flag telling whether all of them could be resolved.

        """
        resolved: list[str] = []
        all_resolved = True
        for arg in args:
            replaced = self.replace_variables(arg)
            if replaced is None:
                all_resolved = False
                resolved.append(arg)
            else:
                resolved.append(replaced)
        return tuple(resolved), all_resolved

    @staticmethod
    def _is_module_library(name: str) -> bool:
        """
        Check if the library is imported using a module name instead of a path.

        Standard libraries are always imported by name and are never searched for in the project.

        Returns:
            True if the import should be looked up as a Python module.

        """
        if name in STDLIBS:
            return True
        return not name.endswith(LIBRARY_FILE_SUFFIXES) and "/" not in name and "\\" not in name

    def _find_module_library(self, name: str) -> Path | None:
        """
        Find a library imported by a module name in the search paths.

        Both ``MyLibrary`` and ``my_package.MyLibrary`` forms are supported, as well as libraries implemented as
        packages. Standard libraries are never searched for, since they are not part of the project.

        Returns:
            Path to the library file, or None if it is not found in the search paths.

        """
        if name in STDLIBS:
            return None
        relative = Path(*name.split("."))
        for search_path in self.search_paths:
            for candidate in (search_path / f"{relative}.py", search_path / relative / "__init__.py"):
                if candidate.is_file():
                    return candidate.resolve()
        return None

    def _find_path(self, name: str, base_dir: Path) -> Path | None:
        """
        Find the file the import points to.

        Relative paths are resolved against the directory of the importing file, matching Robot Framework behaviour.
        If the file is not found there, the configured search paths are used.

        Returns:
            Path to the existing file, or None if it does not exist.

        """
        path = Path(name.replace("\\", "/"))
        if path.is_absolute():
            return self._existing_file(path)
        for directory in (base_dir, *self.search_paths):
            found = self._existing_file(directory / path)
            if found is not None:
                return found
        return None

    @staticmethod
    def _existing_file(candidate: Path) -> Path | None:
        """
        Return the resolved path if it points to an existing file.

        Returns:
            Resolved path, or None if it is not an existing file.

        """
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:  # pragma: no cover - defensive, invalid path characters
            return None
        return None
