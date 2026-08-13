"""Data classes describing keywords, variables and imports found in the project."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from robot.errors import DataError
from robot.running.arguments import EmbeddedArguments, UserKeywordArgumentParser

from robocop.linter.utils.misc import normalize_robot_name
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    import re
    from pathlib import Path

    from robot.parsing.model.blocks import Keyword
    from robot.parsing.model.statements import LibraryImport, ResourceImport, Statement, VariablesImport


def parse_embedded_arguments(name: str) -> EmbeddedArguments | None:
    """
    Parse embedded arguments from the keyword name.

    Returns:
        EmbeddedArguments if the name contains embedded arguments, otherwise None.

    """
    try:
        if ROBOT_VERSION.major < 6:
            embedded = EmbeddedArguments(name)
        else:
            embedded = EmbeddedArguments.from_name(name)
    except (DataError, ValueError):
        return None
    if embedded and embedded.args:
        return embedded
    return None


@dataclass(frozen=True)
class Location:
    """Position of the definition or usage inside the source file."""

    source: Path
    lineno: int
    col: int
    end_lineno: int
    end_col: int


@dataclass(frozen=True)
class ArgumentsSpec:
    """
    Argument specification of the user keyword, parsed from the ``[Arguments]`` setting.

    The specification is built from the abstract syntax tree only. No library is imported and no user code is
    executed to retrieve it.
    """

    positional: tuple[str, ...] = ()
    defaults: frozenset[str] = frozenset()
    var_positional: str | None = None
    var_named: str | None = None
    named_only: tuple[str, ...] = ()

    @property
    def min_args(self) -> int:
        """Minimal number of positional arguments accepted by the keyword."""
        return len([arg for arg in self.positional if arg not in self.defaults])

    @property
    def max_args(self) -> int | None:
        """Maximum number of positional arguments, or None if the keyword accepts any number of them."""
        if self.var_positional is not None:
            return None
        return len(self.positional)

    @property
    def accepts_named(self) -> bool:
        """Whether the keyword accepts arbitrary named arguments (``&{kwargs}``)."""
        return self.var_named is not None

    @classmethod
    def from_arguments(cls, arguments: list[str]) -> ArgumentsSpec:
        """
        Build the specification from raw ``[Arguments]`` values.

        Returns:
            ArgumentsSpec built from the argument values, empty spec if they cannot be parsed.

        """
        try:
            spec = UserKeywordArgumentParser().parse(arguments)
        except DataError:
            return cls()
        return cls(
            positional=tuple(spec.positional),
            defaults=frozenset(spec.defaults),
            var_positional=spec.var_positional,
            var_named=spec.var_named,
            named_only=tuple(spec.named_only),
        )


@dataclass
class KeywordDefinition:
    """User keyword defined in a suite, resource file or an init file."""

    name: str
    normalized_name: str
    location: Location
    node: Keyword
    arguments: ArgumentsSpec = field(default_factory=ArgumentsSpec)
    embedded: re.Pattern[str] | None = None
    is_private: bool = False

    @property
    def has_embedded_arguments(self) -> bool:
        return self.embedded is not None

    def matches(self, name: str) -> bool:
        """
        Check if the keyword definition can be called using given name.

        Returns:
            True if the name matches this definition.

        """
        if self.embedded is not None:
            return bool(self.embedded.fullmatch(name))
        return normalize_robot_name(name) == self.normalized_name


@dataclass
class KeywordUsage:
    """Single place where a keyword is called."""

    name: str
    normalized_name: str
    location: Location
    argument_count: int = 0
    named_arguments: tuple[str, ...] = ()
    name_contains_variable: bool = False
    """Keyword is called using a name built from a variable. Its definition cannot be found statically."""


@dataclass
class VariableDefinition:
    """Variable defined in the ``*** Variables ***`` section or on the command line."""

    name: str
    normalized_name: str
    value: str | None = None
    location: Location | None = None


class ImportType(str, Enum):
    """Type of the import from the ``*** Settings ***`` section."""

    LIBRARY = "Library"
    RESOURCE = "Resource"
    VARIABLES = "Variables"


class ImportStatus(str, Enum):
    """Outcome of resolving an import."""

    RESOLVED = "resolved"
    """Import points to an existing file."""
    NOT_FOUND = "not_found"
    """Import was fully resolved to a path, but the path does not exist."""
    UNRESOLVABLE = "unresolvable"
    """Import name contains variables that could not be resolved. Nothing can be said about it."""
    EXTERNAL = "external"
    """Import does not point to a file in the project, for example a library installed as a Python module."""


@dataclass
class ResolvedImport:
    """Result of resolving a single ``Library``, ``Resource`` or ``Variables`` import."""

    import_type: ImportType
    name: str
    """Import name as written in the source code, before resolving variables."""
    resolved_name: str
    """Import name after resolving variables. Same as ``name`` if there was nothing to resolve."""
    status: ImportStatus
    location: Location
    path: Path | None = None
    node: LibraryImport | ResourceImport | VariablesImport | Statement | None = None
    error: str | None = None

    @property
    def is_resolved(self) -> bool:
        return self.status == ImportStatus.RESOLVED
