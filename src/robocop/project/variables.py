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

    Layers are searched from the highest to the lowest precedence: command line, own (``*** Variables ***`` section
    of the file itself), imported (from resource and variable files) and built-in.
    """

    def __init__(self, source: Path | None = None) -> None:
        self.source = source
        self._command_line: dict[str, str] = {}
        self._own: dict[str, str] = {}
        self._imported: dict[str, str] = {}

    def add_command_line(self, variables: dict[str, str]) -> None:
        """Add variables provided with the ``--variable`` option."""
        for name, value in variables.items():
            self._command_line[normalize_robot_name(name)] = value

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
        for layer in (self._builtin_variables(), self._imported, self._own, self._command_line):
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
