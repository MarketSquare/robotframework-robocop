"""Collecting keyword definitions, keyword usages, variables and imports from a single model."""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from robot.api import Token
from robot.api.parsing import ModelVisitor
from robot.parsing.model.statements import Arguments, Statement, Tags
from robot.variables.search import search_variable

from robocop.linter.utils.misc import normalize_robot_name
from robocop.parsing.run_keywords import BDD_PREFIXES, iterate_keyword_calls
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]
from robocop.project.definitions import (
    ArgumentsSpec,
    ImportType,
    KeywordDefinition,
    KeywordUsage,
    Location,
    VariableDefinition,
    embedded_name_pattern,
)

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model.blocks import File, Keyword, Section
    from robot.parsing.model.statements import (
        KeywordCall,
        LibraryImport,
        ResourceImport,
        Setup,
        Template,
        Variable,
        VariablesImport,
    )


DEFAULT_BDD_PREFIXES = BDD_PREFIXES
VARIABLE_VALUE_TOKENS = (Token.ARGUMENT, Token.NAME, Token.KEYWORD, Token.OPTION)


@dataclass
class RawImport:
    """Import statement before it is resolved to a path."""

    import_type: ImportType
    name: str
    location: Location
    args: tuple[str, ...] = ()
    """Arguments of the ``Library`` import."""
    alias: str | None = None
    """Name the library was imported with (``AS`` / ``WITH NAME``)."""


@dataclass
class CollectedFile:
    """Everything collected from a single source file."""

    path: Path
    is_suite: bool = False
    is_init_file: bool = False
    keywords: list[KeywordDefinition] = field(default_factory=list)
    usages: list[KeywordUsage] = field(default_factory=list)
    variables: list[VariableDefinition] = field(default_factory=list)
    used_variables: set[str] = field(default_factory=set)
    """Normalized names of variables used anywhere in the file."""
    imports: list[RawImport] = field(default_factory=list)


class ProjectFileCollector(ModelVisitor):  # type: ignore[misc]
    """
    Collects definitions and usages from a single model.

    Only static information is collected. Keywords called through a variable are recorded with the raw name, so rules
    can decide to ignore them instead of reporting a false positive.
    """

    def __init__(self, path: Path, bdd_prefixes: frozenset[str] | None = None) -> None:
        self.collected = CollectedFile(path=path, is_init_file="__init__" in path.name)
        self.bdd_prefixes = bdd_prefixes if bdd_prefixes is not None else DEFAULT_BDD_PREFIXES

    def collect(self, model: File) -> CollectedFile:
        """
        Visit the model and return collected data.

        Returns:
            CollectedFile with keyword definitions, usages, variables and imports.

        """
        self.visit(model)
        for node in ast.walk(model):
            if isinstance(node, Statement):
                self._collect_used_variables(node)
        return self.collected

    def _location(self, node: Statement | Keyword, name_length: int | None = None) -> Location:
        col = node.col_offset + 1
        end_col = col + name_length if name_length is not None else node.end_col_offset + 1
        return Location(
            source=self.collected.path,
            lineno=node.lineno,
            col=col,
            end_lineno=node.lineno,
            end_col=end_col,
        )

    def _token_location(self, token: Token) -> Location:
        return Location(
            source=self.collected.path,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_lineno=token.lineno,
            end_col=token.end_col_offset + 1,
        )

    def visit_TestCaseSection(self, node: Section) -> None:  # noqa: N802
        self.collected.is_suite = True
        self.generic_visit(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        if not node.name:
            return
        embedded = embedded_name_pattern(node.name)
        self.collected.keywords.append(
            KeywordDefinition(
                name=node.name,
                normalized_name=normalize_robot_name(node.name),
                location=self._location(node.header, name_length=len(node.name)),
                arguments=self._keyword_arguments(node),
                embedded=embedded,
                is_private=self._is_private(node),
            )
        )
        self.generic_visit(node)

    @staticmethod
    def _keyword_arguments(node: Keyword) -> ArgumentsSpec:
        for statement in node.body:
            if isinstance(statement, Arguments):
                return ArgumentsSpec.from_arguments([token.value for token in statement.get_tokens(Token.ARGUMENT)])
        return ArgumentsSpec()

    @staticmethod
    def _is_private(node: Keyword) -> bool:
        for statement in node.body:
            if isinstance(statement, Tags) and any(
                token.value == "robot:private" for token in statement.get_tokens(Token.ARGUMENT)
            ):
                return True
        return False

    def visit_Variable(self, node: Variable) -> None:  # noqa: N802
        name_token = node.get_token(Token.VARIABLE)
        if name_token is None:
            return
        match = search_variable(name_token.value, ignore_errors=True)
        if not match.base:
            return
        values = [token.value for token in node.get_tokens(Token.ARGUMENT)]
        self.collected.variables.append(
            VariableDefinition(
                name=match.base,
                normalized_name=normalize_robot_name(match.base),
                value=values[0] if len(values) == 1 else None,
                location=self._token_location(name_token),
            )
        )

    def _add_import(self, import_type: ImportType, node: Statement) -> None:
        name_token = node.get_token(Token.NAME)
        if name_token is None or not name_token.value:
            return
        location = Location(
            source=self.collected.path,
            lineno=name_token.lineno,
            col=name_token.col_offset + 1,
            end_lineno=name_token.lineno,
            end_col=name_token.end_col_offset + 1,
        )
        self.collected.imports.append(
            RawImport(
                import_type=import_type,
                name=name_token.value,
                location=location,
                args=tuple(getattr(node, "args", ()) or ()),
                alias=getattr(node, "alias", None),
            )
        )

    def visit_LibraryImport(self, node: LibraryImport) -> None:  # noqa: N802
        self._add_import(ImportType.LIBRARY, node)

    def visit_ResourceImport(self, node: ResourceImport) -> None:  # noqa: N802
        self._add_import(ImportType.RESOURCE, node)

    def visit_VariablesImport(self, node: VariablesImport) -> None:  # noqa: N802
        self._add_import(ImportType.VARIABLES, node)

    def _collect_used_variables(self, node: Statement) -> None:
        """Record variables used in the statement."""
        for token in node.get_tokens(*VARIABLE_VALUE_TOKENS):
            self._add_used_variables(token.value)

    def _add_used_variables(self, value: str) -> None:
        for match in VariableMatches(value, ignore_errors=True):
            if match.base:
                self.collected.used_variables.add(normalize_robot_name(match.base))
                self._add_used_variables(match.base)

    def _add_usages(self, node: Statement, name_token_type: str) -> None:
        for call in iterate_keyword_calls(node, name_token_type):
            self._add_usage(call.name, list(call.arguments))

    def _add_usage(self, token: Token, arguments: list[Token], is_template: bool = False) -> None:
        if not token.value:
            return
        match = search_variable(token.value, ignore_errors=True)
        self.collected.usages.append(
            KeywordUsage(
                name=token.value,
                normalized_name=normalize_robot_name(token.value),
                location=Location(
                    source=self.collected.path,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_lineno=token.lineno,
                    end_col=token.end_col_offset + 1,
                ),
                arguments=tuple(argument.value for argument in arguments),
                argument_positions=tuple(
                    (argument.lineno, argument.col_offset + 1, argument.end_col_offset + 1) for argument in arguments
                ),
                name_contains_variable=bool(match.base),
                bdd_prefix=self._bdd_prefix(token.value),
                is_template=is_template,
            )
        )

    def _bdd_prefix(self, name: str) -> str | None:
        first_word, separator, _rest = name.partition(" ")
        if not separator:
            return None
        return first_word if first_word.title() in self.bdd_prefixes else None

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        self._add_usages(node, Token.KEYWORD)

    def visit_Setup(self, node: Setup) -> None:  # noqa: N802
        self._add_usages(node, Token.NAME)

    visit_Teardown = visit_Setup  # noqa: N815
    visit_SuiteSetup = visit_Setup  # noqa: N815
    visit_SuiteTeardown = visit_Setup  # noqa: N815
    visit_TestSetup = visit_Setup  # noqa: N815
    visit_TestTeardown = visit_Setup  # noqa: N815

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        if not node.value:
            return
        name_token = node.get_token(Token.NAME)
        if name_token is not None:
            self._add_usage(name_token, [], is_template=True)

    visit_TestTemplate = visit_Template  # noqa: N815
