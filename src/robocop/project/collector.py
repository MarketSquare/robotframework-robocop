"""Collecting keyword definitions, keyword usages, variables and imports from a single model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from robot.api import Token
from robot.api.parsing import ModelVisitor
from robot.parsing.model.statements import Arguments, Tags
from robot.variables.search import search_variable

from robocop.linter.utils.misc import normalize_robot_name
from robocop.parsing.run_keywords import iterate_keyword_names
from robocop.project.definitions import (
    ArgumentsSpec,
    ImportType,
    KeywordDefinition,
    KeywordUsage,
    Location,
    VariableDefinition,
    parse_embedded_arguments,
)

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model.blocks import File, Keyword, Section
    from robot.parsing.model.statements import (
        KeywordCall,
        LibraryImport,
        ResourceImport,
        Setup,
        Statement,
        Template,
        Variable,
        VariablesImport,
    )


@dataclass
class RawImport:
    """Import statement before it is resolved to a path."""

    import_type: ImportType
    name: str
    location: Location
    node: Statement


@dataclass
class CollectedFile:
    """Everything collected from a single source file."""

    path: Path
    is_suite: bool = False
    is_init_file: bool = False
    keywords: list[KeywordDefinition] = field(default_factory=list)
    usages: list[KeywordUsage] = field(default_factory=list)
    variables: list[VariableDefinition] = field(default_factory=list)
    imports: list[RawImport] = field(default_factory=list)


class ProjectFileCollector(ModelVisitor):  # type: ignore[misc]
    """
    Collects definitions and usages from a single model.

    Only static information is collected. Keywords called through a variable are recorded with the raw name, so rules
    can decide to ignore them instead of reporting a false positive.
    """

    def __init__(self, path: Path) -> None:
        self.collected = CollectedFile(path=path, is_init_file="__init__" in path.name)

    def collect(self, model: File) -> CollectedFile:
        """
        Visit the model and return collected data.

        Returns:
            CollectedFile with keyword definitions, usages, variables and imports.

        """
        self.visit(model)
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

    def visit_TestCaseSection(self, node: Section) -> None:  # noqa: N802
        self.collected.is_suite = True
        self.generic_visit(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        if not node.name:
            return
        embedded = parse_embedded_arguments(node.name)
        self.collected.keywords.append(
            KeywordDefinition(
                name=node.name,
                normalized_name=normalize_robot_name(node.name),
                location=self._location(node.header, name_length=len(node.name)),
                node=node,
                arguments=self._keyword_arguments(node),
                embedded=embedded.name if embedded is not None else None,
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
                location=self._location(node),
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
            RawImport(import_type=import_type, name=name_token.value, location=location, node=node)
        )

    def visit_LibraryImport(self, node: LibraryImport) -> None:  # noqa: N802
        self._add_import(ImportType.LIBRARY, node)

    def visit_ResourceImport(self, node: ResourceImport) -> None:  # noqa: N802
        self._add_import(ImportType.RESOURCE, node)

    def visit_VariablesImport(self, node: VariablesImport) -> None:  # noqa: N802
        self._add_import(ImportType.VARIABLES, node)

    def _add_usages(self, node: Statement, name_token_type: str) -> None:
        for token in iterate_keyword_names(node, name_token_type):
            self._add_usage(token, node)

    def _add_usage(self, token: Token, node: Statement) -> None:
        if not token.value:
            return
        match = search_variable(token.value, ignore_errors=True)
        arguments = [arg.value for arg in node.get_tokens(Token.ARGUMENT)]
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
                argument_count=len(arguments),
                named_arguments=tuple(arg.split("=", maxsplit=1)[0] for arg in arguments if "=" in arg),
                name_contains_variable=bool(match.base),
            )
        )

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
            self._add_usage(name_token, node)

    visit_TestTemplate = visit_Template  # noqa: N815
