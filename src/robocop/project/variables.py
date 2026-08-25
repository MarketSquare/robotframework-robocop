"""
Variable scope used when resolving import paths.

Modelled after Robot Framework's own variable precedence. Variables set on the command line take precedence over
variables defined in the file itself, which take precedence over variables coming from imported resource and
variable files. Built-in variables such as ``${CURDIR}`` have the lowest precedence.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from robot.errors import DataError
from robot.variables import Variables

from robocop.linter.utils.misc import normalize_robot_name

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robocop.project.definitions import VariableDefinition


class VariableScope:
    """
    Variables visible in a single source file, ordered by precedence.

    Layers are searched from the highest to the lowest precedence: command line, variable files, own
    (``*** Variables ***`` section of the file itself), imported (from resource and variable files) and built-in.
    """

    def __init__(self, source: Path | None = None) -> None:
        self.source = source
        self._command_line: dict[str, str] = {}
        self._variable_files: dict[str, str] = {}
        self._own: dict[str, str] = {}
        self._imported: dict[str, str] = {}

    def add_command_line(self, variables: dict[str, str]) -> None:
        """Add variables provided with the ``--variable`` option."""
        for name, value in variables.items():
            self._command_line[normalize_robot_name(name)] = value

    def add_variable_files(self, paths: list[str], search_paths: list[Path] | None = None) -> None:
        """
        Add variables from files provided with the ``--variablefile`` option.

        Variable files are executed, so a broken file could stop the whole run. Any error is ignored and the file is
        simply skipped, following the rule that project checks never fail because of the analysed project.
        """
        for name, value in load_variable_files(paths, search_paths).items():
            self._variable_files[normalize_robot_name(name)] = value

    def add_own(self, variables: list[VariableDefinition]) -> None:
        """Add variables defined in the ``*** Variables ***`` section of the file itself."""
        for variable in variables:
            if variable.value is not None:
                self._own[variable.normalized_name] = variable.value

    def add_imported(self, variables: list[VariableDefinition]) -> None:
        """Add variables coming from imported resource or variable files."""
        for variable in variables:
            if variable.value is not None:
                self._imported.setdefault(variable.normalized_name, variable.value)

    def copy_for(self, source: Path) -> VariableScope:
        """
        Create a copy of this scope bound to a different source file.

        Used to seed per-file scopes from the global (command line) scope.

        Returns:
            New VariableScope with the same command line variables.

        """
        scope = VariableScope(source)
        scope._command_line = dict(self._command_line)
        scope._variable_files = dict(self._variable_files)
        return scope

    def _builtin_variables(self) -> dict[str, str]:
        """
        Return built-in variables that can be statically resolved.

        Only path related variables have a meaningful static value. ``${CURDIR}`` is resolved relative to the source
        file, exactly like Robot Framework does it.

        Returns:
            Mapping of normalized variable name to its value.

        """
        if self.source is None:
            return {}
        return {
            "curdir": str(self.source.parent),
            "execdir": str(Path.cwd()),
            "tempdir": tempfile.gettempdir(),
        }

    def iter_all(self) -> Iterator[tuple[str, str]]:
        """
        Iterate over all variables from the lowest to the highest precedence.

        Yields:
            Tuples of normalized variable name and its value.

        """
        for layer in (self._builtin_variables(), self._imported, self._own, self._variable_files, self._command_line):
            yield from layer.items()

    def as_robot_variables(self) -> Variables:
        """
        Build a Robot Framework ``Variables`` object out of this scope.

        Later layers overwrite earlier ones, so the resulting object follows the precedence order.

        Returns:
            Variables object that can be used to replace variables in a string.

        """
        variables = Variables()
        for name, value in self.iter_all():
            try:
                variables[f"${{{name}}}"] = value
            except DataError:  # pragma: no cover - defensive, invalid variable name
                continue
        return variables


def load_variable_files(paths: list[str], search_paths: list[Path] | None = None) -> dict[str, str]:
    """
    Load variables from Python and YAML variable files.

    Variable files may take arguments, using the Robot Framework ``path:arg1:arg2`` syntax. Only scalar variables
    are loaded, since only those can be used to build an import path.

    Loading a Python variable file imports it, which executes its code. Errors are ignored so that a broken or
    missing variable file never stops the analysis.

    Returns:
        Mapping of variable name to its value.

    """
    loaded: dict[str, str] = {}
    for entry in paths:
        path, args = _split_variable_file_args(entry, search_paths)
        if path is None:
            continue
        variables = Variables()
        try:
            variables.set_from_file(str(path), args)
        except Exception:  # noqa: BLE001, S112 - variable file may fail in any way, it is never fatal
            continue
        loaded.update(
            {name: value for name, value in variables.as_dict(decoration=False).items() if isinstance(value, str)}
        )
    return loaded


def _split_variable_file_args(entry: str, search_paths: list[Path] | None) -> tuple[Path | None, list[str]]:
    """
    Split variable file definition into the path and its arguments and find the file.

    Returns:
        Tuple of the path to an existing variable file (None if it was not found) and its arguments.

    """
    parts = entry.split(":")
    for split_at in range(len(parts), 0, -1):
        candidate = ":".join(parts[:split_at])
        path = _find_variable_file(candidate, search_paths)
        if path is not None:
            return path, parts[split_at:]
    return None, []


def _find_variable_file(name: str, search_paths: list[Path] | None) -> Path | None:
    """
    Find variable file next to the working directory or in the search paths.

    Returns:
        Path to an existing file, or None if it was not found.

    """
    path = Path(name)
    if path.is_file():
        return path.resolve()
    for search_path in search_paths or []:
        candidate = search_path / path
        if candidate.is_file():
            return candidate.resolve()
    return None
