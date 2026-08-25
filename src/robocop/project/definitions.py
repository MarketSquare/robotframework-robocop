"""Data classes describing keywords, variables and imports found in the project."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

from robot.errors import DataError
from robot.running.arguments import EmbeddedArguments, UserKeywordArgumentParser
from robot.variables.search import search_variable

from robocop.files import resolve_path
from robocop.linter.utils.misc import normalize_robot_name
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


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


def embedded_name_pattern(name: str) -> re.Pattern[str] | None:
    """
    Build a pattern matching keyword names that can be called using keyword with embedded arguments.

    Returns:
        Compiled pattern, or None if the name does not contain embedded arguments.

    """
    embedded = parse_embedded_arguments(name)
    return embedded.name if embedded is not None else None


def usage_name_pattern(name: str) -> re.Pattern[str] | None:
    """
    Build a pattern matching keyword names that a dynamic call may refer to.

    Variables in the name are replaced with a wildcard, so a call to ``Login ${type}`` matches both ``Login Admin``
    and ``Login User``. The pattern is matched against normalized keyword names.

    Returns:
        Compiled pattern, or None if the name consists of a variable only and would match everything.

    """
    normalized = normalize_robot_name(name)
    pattern_parts: list[str] = []
    remaining = normalized
    only_variables = True
    while remaining:
        match = search_variable(remaining, ignore_errors=True)
        if match.base is None:
            pattern_parts.append(re.escape(remaining))
            only_variables = False
            break
        if match.before:
            pattern_parts.append(re.escape(match.before))
            only_variables = False
        pattern_parts.append(".*")
        remaining = match.after
    if only_variables:
        return None
    return re.compile("".join(pattern_parts))


@dataclass(frozen=True)
class Location:
    """Position of the definition or usage inside the source file."""

    source: Path
    lineno: int
    col: int
    end_lineno: int
    end_col: int


@dataclass(frozen=True)
class ArgumentsMismatch:
    """Difference between the keyword definition and the arguments used in a call."""

    expected: str
    """Human readable description of the accepted number of arguments."""
    provided: int
    """Number of positional arguments used in the call."""
    missing: tuple[str, ...] = ()
    """Names of required arguments that were not provided."""


def _split_named_argument(argument: str) -> tuple[str, str] | None:
    """
    Split ``name=value`` argument into name and value, respecting escaped equal signs.

    Returns:
        Tuple of name and value, or None if the argument is not in the ``name=value`` format.

    """
    escaped = False
    for index, char in enumerate(argument):
        if escaped:
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "=":
            return argument[:index], argument[index + 1 :]
    return None


@dataclass(frozen=True)
class ArgumentsSpec:
    """
    Argument specification of the keyword.

    For keywords defined in the project it is built from the ``[Arguments]`` setting using the abstract syntax tree
    only. For keywords coming from libraries it is read from the imported library.
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

    def _known_names(self) -> dict[str, str]:
        return {normalize_robot_name(name): name for name in (*self.positional, *self.named_only)}

    def describe_accepted(self) -> str:
        """
        Describe the number of accepted arguments, using wording similar to Robot Framework errors.

        Returns:
            Description such as ``1 argument`` or ``from 1 to 2 arguments``.

        """
        positional = self._describe_positional()
        required_named_only = [name for name in self.named_only if name not in self.defaults]
        if not required_named_only:
            return positional
        names = ", ".join(f"${{{name}}}" for name in required_named_only)
        plural = "" if len(required_named_only) == 1 else "s"
        return f"{positional} and named-only argument{plural} {names}"

    def _describe_positional(self) -> str:
        minimum = self.min_args
        maximum = self.max_args
        if maximum is None:
            return f"at least {minimum} argument{'' if minimum == 1 else 's'}"
        if minimum == maximum:
            return f"{minimum} argument{'' if minimum == 1 else 's'}"
        return f"from {minimum} to {maximum} arguments"

    def validate_call(self, arguments: Sequence[str]) -> ArgumentsMismatch | None:
        """
        Validate arguments used in a keyword call against this specification.

        Returns None when the call is valid, and also when it cannot be validated with certainty, for example when
        an argument is a name built from a variable.

        Returns:
            ArgumentsMismatch describing the problem, or None if the call is valid or cannot be validated.

        """
        known_names = self._known_names()
        positional_values: list[str] = []
        named_names: set[str] = set()
        for argument in arguments:
            split = _split_named_argument(argument)
            if split is None:
                positional_values.append(argument)
                continue
            name, _value = split
            if search_variable(name, ignore_errors=True).base is not None:
                return None  # named argument built from a variable, anything is possible
            normalized = normalize_robot_name(name)
            if normalized in known_names:
                named_names.add(known_names[normalized])
            elif self.accepts_named:
                named_names.add(name)
            else:
                positional_values.append(argument)
        return self._compare(positional_values, named_names)

    def name_positional_arguments(self, arguments: Sequence[str]) -> list[tuple[int, str]] | None:
        """
        Match arguments passed by the position in the call with the names from this specification.

        Returns:
            List of ``(index in the call, argument name)`` pairs, or None if the call cannot be analyzed
            with certainty.

        """
        known_names = self._known_names()
        positional_arguments: list[tuple[int, str]] = []
        used_named = False
        for index, argument in enumerate(arguments):
            split = _split_named_argument(argument)
            if split is not None:
                name, _value = split
                if search_variable(name, ignore_errors=True).base is not None:
                    return None  # named argument built from a variable, anything is possible
                if normalize_robot_name(name) in known_names or self.accepts_named:
                    used_named = True
                    continue
            if used_named:
                return None  # positional argument after a named one, such call is invalid anyway
            if len(positional_arguments) >= len(self.positional):
                return None  # argument is passed to the ``*varargs`` and cannot be named
            positional_arguments.append((index, self.positional[len(positional_arguments)]))
        return positional_arguments

    def _compare(self, positional_values: list[str], named_names: set[str]) -> ArgumentsMismatch | None:
        provided = len(positional_values)
        maximum = self.max_args
        if maximum is not None and provided > maximum:
            return ArgumentsMismatch(expected=self.describe_accepted(), provided=provided)
        filled_by_position = set(self.positional[:provided])
        if filled_by_position & named_names:
            return None  # argument given twice, Robot Framework reports it on its own
        required = [name for name in (*self.positional, *self.named_only) if name not in self.defaults]
        missing = [name for name in required if name not in filled_by_position and name not in named_names]
        if missing:
            return ArgumentsMismatch(expected=self.describe_accepted(), provided=provided, missing=tuple(missing))
        return None


@dataclass
class KeywordDefinition:
    """Keyword defined in a suite, resource file, init file or in an imported library."""

    name: str
    normalized_name: str
    location: Location
    arguments: ArgumentsSpec = field(default_factory=ArgumentsSpec)
    embedded: re.Pattern[str] | None = None
    is_private: bool = False
    library_name: str | None = None
    """Name of the library the keyword comes from. None for keywords defined in the project files."""

    @property
    def is_from_library(self) -> bool:
        return self.library_name is not None

    @property
    def has_embedded_arguments(self) -> bool:
        return self.embedded is not None

    @property
    def owner_name(self) -> str:
        """Name of the library or resource file the keyword can be prefixed with."""
        return self.library_name or self.location.source.stem

    def matches_owner(self, prefix: str) -> bool:
        """
        Check if given resource or library prefix points to the owner of this keyword.

        Libraries inside a module can be prefixed both with the full name (``module.Library``) and with the
        library name only (``Library``).

        Returns:
            True if the prefix can be used to call this definition.

        """
        owner = normalize_robot_name(self.owner_name)
        normalized = normalize_robot_name(prefix)
        return owner == normalized or owner.endswith(f".{normalized}")

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
    arguments: tuple[str, ...] = ()
    """Raw values of the arguments used in this call."""
    argument_positions: tuple[tuple[int, int, int], ...] = ()
    """Position of every argument in the source file, as a ``(line, column, end column)`` tuple."""
    name_contains_variable: bool = False
    """Keyword is called using a name built from a variable. Its definition cannot be found statically."""
    bdd_prefix: str | None = None
    """BDD prefix (``Given``, ``When``, ...) removed from the name, if there was one."""
    is_template: bool = False
    """Keyword is used as a test template. Its arguments come from the test case body, not from the setting."""

    @property
    def argument_count(self) -> int:
        """Number of arguments used in this call."""
        return len(self.arguments)

    @property
    def has_argument_expansion(self) -> bool:
        """
        Whether any argument expands a list or a dictionary variable.

        The real number of arguments is only known at runtime, so such calls cannot be validated statically.
        """
        return any(_is_expanded_argument(argument) for argument in self.arguments)

    def names_to_check(self) -> tuple[str, ...]:
        """
        Names this call may refer to.

        A call using a BDD prefix may refer both to the keyword with the prefix and to the one without it.

        Returns:
            Tuple of names, most specific first.

        """
        if self.bdd_prefix is None:
            return (self.name,)
        return (self.name, self.name[len(self.bdd_prefix) :].lstrip())


def _is_expanded_argument(argument: str) -> bool:
    match = search_variable(argument, ignore_errors=True)
    return match.identifier in {"@", "&"} and match.is_variable()


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
    error: str | None = None
    args: tuple[str, ...] = ()
    """Arguments of the ``Library`` import, with variables resolved."""
    alias: str | None = None
    """Name the library was imported with (``AS`` / ``WITH NAME``)."""
    args_resolved: bool = True
    """Whether all variables used in the import arguments could be resolved."""
    _resolved_path: Path | None = field(default=None, repr=False, compare=False)

    @property
    def resolved_path(self) -> Path | None:
        """Resolved path the import points to, computed once per import."""
        if self.path is None:
            return None
        if self._resolved_path is None:
            self._resolved_path = resolve_path(self.path)
        return self._resolved_path

    @property
    def is_resolved(self) -> bool:
        return self.status == ImportStatus.RESOLVED
