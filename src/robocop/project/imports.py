"""
Resolving ``Library``, ``Resource`` and ``Variables`` imports to paths on the disk.

Variables inside the import name are resolved using Robot Framework's own variable machinery, so escaping, nested
variables and environment variables (``%{VAR}`` and ``%{VAR=default}``) behave exactly like during the execution.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from robot.errors import DataError
from robot.libraries import STDLIBS
from robot.variables.search import contains_variable

from robocop.project.definitions import ImportStatus, ImportType, ResolvedImport

if TYPE_CHECKING:
    from robocop.project.definitions import Location
    from robocop.project.variables import VariableScope


class ImportResolver:
    """Resolves import names to paths, using variables visible in the importing file."""

    def __init__(self, scope: VariableScope) -> None:
        self.scope = scope

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
    ) -> ResolvedImport:
        """
        Resolve a single import.

        Args:
            import_type: Type of the import.
            name: Import name as written in the source code.
            location: Position of the import in the source file.
            base_dir: Directory of the file containing the import.

        Returns:
            ResolvedImport describing the outcome.

        """
        resolved_name = self.replace_variables(name)
        if resolved_name is None:
            return ResolvedImport(
                import_type=import_type,
                name=name,
                resolved_name=name,
                status=ImportStatus.UNRESOLVABLE,
                location=location,
                error="Import name contains variables that cannot be resolved statically",
            )
        if import_type == ImportType.LIBRARY and self._is_external_library(resolved_name):
            return ResolvedImport(
                import_type=import_type,
                name=name,
                resolved_name=resolved_name,
                status=ImportStatus.EXTERNAL,
                location=location,
            )
        path = self._find_path(resolved_name, base_dir)
        if path is None:
            return ResolvedImport(
                import_type=import_type,
                name=name,
                resolved_name=resolved_name,
                status=ImportStatus.NOT_FOUND,
                location=location,
            )
        return ResolvedImport(
            import_type=import_type,
            name=name,
            resolved_name=resolved_name,
            status=ImportStatus.RESOLVED,
            location=location,
            path=path,
        )

    @staticmethod
    def _is_external_library(name: str) -> bool:
        """
        Check if the library import points outside the project.

        Standard libraries and libraries imported using a Python module path (``my_package.MyLibrary``) are not files
        in the project and cannot be resolved to a path without importing them.

        Returns:
            True if the import should not be resolved to a path.

        """
        if name in STDLIBS:
            return True
        return not name.endswith((".py", ".class", ".java")) and "/" not in name and "\\" not in name

    @staticmethod
    def _find_path(name: str, base_dir: Path) -> Path | None:
        """
        Find the file the import points to.

        Relative paths are resolved against the directory of the importing file, matching Robot Framework behaviour.

        Returns:
            Path to the existing file, or None if it does not exist.

        """
        path = Path(name.replace("\\", "/"))
        candidate = path if path.is_absolute() else base_dir / path
        try:
            if candidate.is_file():
                return candidate.resolve()
        except OSError:  # pragma: no cover - defensive, invalid path characters
            return None
        return None
