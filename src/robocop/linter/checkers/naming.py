"""Checkers for the rules defined in ``robocop.linter.rules.naming``."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.statements import Arguments
from robot.variables.search import search_variable

from robocop.linter.rules import VisitorChecker, variables
from robocop.linter.rules.naming import SET_VARIABLE_VARIANTS
from robocop.linter.utils import misc as utils
from robocop.version_handling import ROBOT_VERSION, TYPE_SUPPORTED

if TYPE_CHECKING:
    from collections.abc import Iterable

    from robot.parsing.model.blocks import For, If, Keyword, TestCase, While
    from robot.parsing.model.statements import (
        KeywordCall,
        Node,
        Return,
        Var,
    )


class SimilarVariableChecker(VisitorChecker):
    """Checker for finding same variables with similar names."""

    possible_variable_overwriting: variables.PossibleVariableOverwritingRule
    inconsistent_variable_name: variables.InconsistentVariableNameRule

    _VAR_PATTERN = re.compile(r"[$@%&]\{([^{}]+)}")

    def __init__(self) -> None:
        self.assigned_variables: defaultdict[str, list[str]] = defaultdict(list)
        self.parent_name = ""
        self.parent_type = ""
        super().__init__()

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        self.visit_vars_and_find_similar(node)
        self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.assigned_variables = defaultdict(list)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        self.generic_visit(node)

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if utils.normalize_robot_name(node.keyword, remove_prefix="builtin.") in SET_VARIABLE_VARIANTS:
            normalized, assign_value = "", ""
            for index, token in enumerate(node.data_tokens[1:]):
                if index == 0:  # First argument is assign-like
                    normalized = utils.normalize_robot_var_name(token.value)
                    assign_value = token.value  # process assign last, cache for now
                else:
                    self.find_not_nested_variable(token)
            if assign_value:
                variable = search_variable(assign_value, ignore_errors=True)
                self.assigned_variables[normalized].append(variable.base)
        else:
            for token in node.get_tokens(Token.ARGUMENT, Token.KEYWORD):  # argument can be used in keyword name
                self.find_not_nested_variable(token)
        tokens = node.get_tokens(Token.ASSIGN)
        self.find_similar_variables(tokens, node)

    def visit_Var(self, node: Var) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg)
        variable = node.get_token(Token.VARIABLE)
        if variable:
            self.find_similar_variables([variable], node, ignore_overwriting=not utils.is_var_scope_local(node))

    def visit_If(self, node: If) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token)
        tokens = node.header.get_tokens(Token.ASSIGN)
        self.find_similar_variables(tokens, node)
        self.generic_visit(node)

    def visit_While(self, node: While) -> While:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token)
        return self.generic_visit(node)

    @staticmethod
    def for_assign_vars(for_node: For) -> Iterable[str]:
        if ROBOT_VERSION.major < 7:
            yield from for_node.variables
        else:
            yield from for_node.assign

    def visit_For(self, node: For) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token)
        for var in self.for_assign_vars(node):
            variable = search_variable(var, ignore_errors=True)
            self.assigned_variables[utils.normalize_robot_var_name(var)].append(variable.base)
        self.generic_visit(node)

    visit_ForLoop = visit_For  # noqa: N815

    def visit_Return(self, node: Return) -> None:  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token)

    visit_ReturnStatement = visit_Teardown = visit_Timeout = visit_Return  # noqa: N815

    def parse_embedded_arguments(self, name_token: Token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        if "$" not in name_token.value:
            return
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    var_name, *pattern = token.value.split(":", maxsplit=1)
                    if pattern:
                        var_name = var_name + "}"  # recreate, so it handles ${variable:pattern} -> ${variable} matching
                    normalized_name = utils.normalize_robot_var_name(var_name)
                    variable = search_variable(var_name, ignore_errors=True)
                    self.assigned_variables[normalized_name].append(variable.base)
        except VariableError:
            pass

    def check_inconsistent_naming(self, token: Token, value: str, offset: int) -> None:
        """
        Check if the variable name ``value`` was already defined under a matching but different name.

        :param token: ast token representing the string with variable
        :param value: name of variable found in token value string
        :param offset: starting position of variable in token value string
        """
        # TODO: Does not support item access, combine with other rules
        if TYPE_SUPPORTED:
            value_no_type, *_ = value.split(": ", maxsplit=1)
        else:
            value_no_type = value
        normalized = utils.normalize_robot_name(value_no_type)
        if normalized not in self.assigned_variables:
            return  # we could handle attr access here, ignoring now
        latest_assign = self.assigned_variables[normalized][-1]
        if value_no_type != latest_assign:
            name = "${" + value + "}"
            self.report(
                self.inconsistent_variable_name,
                name=name,
                first_use=f"${{{latest_assign}}}",
                node=token,
                lineno=token.lineno,
                col=token.col_offset + offset + 1,
                end_col=token.col_offset + offset + len(name) + 1,
            )

    def find_not_nested_variable(self, token: Token) -> None:
        r"""
        Find and process not nested variable.

        Search `value` string until there is ${variable} without other variables inside.
        Unescaped escaped syntax ($var or \\${var}) is ignored.
        """
        for match in self._VAR_PATTERN.finditer(token.value):
            self.check_inconsistent_naming(token, match.group(1), match.start(1) - 2)

    def visit_vars_and_find_similar(self, node: Node) -> None:
        """
        Collect all the variations of the variables assigned in the node.

        Update a dictionary `assign_variables` with normalized variable name as a key
        and ads a list of all detected variations of this variable in the node as a value,
        then it checks if similar variable was found.
        """
        for child in node.body:
            # read arguments from Keywords
            if isinstance(child, Arguments):
                for token in child.get_tokens(Token.ARGUMENT):
                    variable_match = search_variable(token.value, ignore_errors=True)
                    normalized = utils.normalize_robot_name(variable_match.base)
                    self.assigned_variables[normalized].append(variable_match.base)

    def find_similar_variables(self, tokens: list[Token], node: Node, ignore_overwriting: bool = False) -> None:
        for token in tokens:
            variable_match = search_variable(token.value, ignore_errors=True)
            name = variable_match.base
            if TYPE_SUPPORTED:
                name, *_ = name.split(": ", maxsplit=1)
            normalized = utils.normalize_robot_name(name)
            if (
                not ignore_overwriting
                and normalized in self.assigned_variables
                and name not in self.assigned_variables[normalized]
            ):
                self.report(
                    self.possible_variable_overwriting,
                    variable_name=variable_match.name,
                    block_name=self.parent_name,
                    block_type=self.parent_type,
                    node=node,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )
            self.assigned_variables[normalized].append(name)
