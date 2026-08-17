"""Checker for automatic variables with context-dependent availability."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from robot.api import Token
from robot.api.parsing import ModelVisitor
from robot.variables.search import search_variable

from robocop.linter.rules import VisitorChecker, variables
from robocop.linter.utils import misc as utils
from robocop.parsing.variables import VariableMatches  # type: ignore[attr-defined]
from robocop.version_handling import ROBOT_VERSION, TYPE_SUPPORTED, Version

if TYPE_CHECKING:
    from collections.abc import Iterator

    from robot.parsing.model.blocks import Keyword, TestCase
    from robot.parsing.model.statements import Node, Statement
    from robot.variables.search import VariableMatch

VariableKey = tuple[str, str]
BindingScope = Literal["local", "suite"]

SET_VARIABLE_SCOPES: dict[str, BindingScope] = {
    "setlocalvariable": "local",
    "settestvariable": "local",
    "settaskvariable": "local",
    "setsuitevariable": "suite",
    "setglobalvariable": "suite",
}


def variable_key(value: str, *, allow_short_syntax: bool = False) -> VariableKey | None:
    """Return the exact identifier/name pair created by a static variable binding."""
    value = utils.strip_equals_from_assignment(value).lstrip("\\")
    variable_match = (
        search_variable(value, ignore_errors=True, parse_type=True)
        if TYPE_SUPPORTED
        else search_variable(value, ignore_errors=True)
    )
    if variable_match.base is not None:
        if variable_match.before or variable_match.after or variable_match.items:
            return None
        identifier = variable_match.identifier
        name = variable_match.base
    elif allow_short_syntax and value.startswith(("$", "@", "&")) and not value.startswith(("${", "@{", "&{")):
        identifier = value[0]
        name = value[1:]
    else:
        return None
    key = (identifier, utils.normalize_robot_name(utils.remove_variable_type_conversion(name)))
    return key if key in variables.AutomaticVariableNotAvailableRule.scopes else None


def setter_scope(node: Statement) -> BindingScope | None:
    """Return the scope created by a statically recognizable BuiltIn setter call."""
    name = getattr(node, "keyword", None) or getattr(node, "name", None)
    if not name:
        return None
    normalized_name = utils.normalize_robot_name(name, remove_prefix="builtin.")
    return SET_VARIABLE_SCOPES.get(normalized_name)


def var_scope(node: Statement) -> BindingScope | None:
    """Return the effective scope of a valid RF 7 VAR statement."""
    if type(node).__name__ != "Var" or node.errors:
        return None
    scope = (getattr(node, "scope", None) or "LOCAL").upper()
    if scope == "SUITES" and Version("7.1") > ROBOT_VERSION:
        return None
    return "suite" if scope in {"SUITE", "SUITES", "GLOBAL"} else "local"


def statement_bindings(node: Statement) -> Iterator[tuple[VariableKey, BindingScope]]:
    """Yield reserved-name bindings created by a statement."""
    node_type = type(node).__name__
    if node_type == "Variable":
        scope: BindingScope | None = "suite"
        tokens = node.get_tokens(Token.VARIABLE)
    elif (scope := setter_scope(node)) is not None:
        argument = node.get_token(Token.ARGUMENT)
        tokens = [argument] if argument is not None else []
    elif (scope := var_scope(node)) is not None:
        tokens = node.get_tokens(Token.VARIABLE)
    elif node_type in {"ForHeader", "ExceptHeader"}:
        scope = "local"
        tokens = node.get_tokens(Token.VARIABLE)
    else:
        scope = "local"
        tokens = node.get_tokens(Token.ASSIGN)
    if scope is None:
        return
    for token in tokens:
        if key := variable_key(token.value, allow_short_syntax=setter_scope(node) is not None):
            yield key, scope


class AutomaticVariableBindingsCollector(ModelVisitor):  # type: ignore[misc]
    """Precollect bindings needed for contexts whose runtime order differs from AST order."""

    def __init__(self) -> None:
        self.section: set[VariableKey] = set()
        self.suite_setup: set[VariableKey] = set()
        self.default_test_setup_local: set[VariableKey] = set()
        self.default_test_setup_suite: set[VariableKey] = set()
        self.default_test_teardown_suite: set[VariableKey] = set()
        self.suite_teardown: set[VariableKey] = set()
        self.test: dict[int, set[VariableKey]] = {}
        self.test_setup_local: dict[int, set[VariableKey]] = {}
        self.test_setup_suite: dict[int, set[VariableKey]] = {}
        self.test_teardown_suite: dict[int, set[VariableKey]] = {}
        self.current_test: TestCase | None = None

    @property
    def default_test_teardown(self) -> set[VariableKey]:
        bindings = self.section | self.suite_setup | self.default_test_setup_local | self.default_test_setup_suite
        for test_bindings in self.test.values():
            bindings |= test_bindings
        return bindings

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        """Keyword call context is not known at the definition site."""

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.current_test = node
        self.test[id(node)] = set()
        self.test_setup_local[id(node)] = set()
        self.test_setup_suite[id(node)] = set()
        self.test_teardown_suite[id(node)] = set()
        self.generic_visit(node)
        self.current_test = None

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        node_type = type(node).__name__
        for key, scope in statement_bindings(node):
            if node_type == "Variable":
                self.section.add(key)
                self.suite_teardown.add(key)
            elif self.current_test is not None:
                if node_type == "Teardown":
                    if scope == "suite":
                        self.test_teardown_suite[id(self.current_test)].add(key)
                        self.suite_teardown.add(key)
                else:
                    self.test[id(self.current_test)].add(key)
                    if node_type == "Setup":
                        local_setup_bindings = self.test_setup_suite if scope == "suite" else self.test_setup_local
                        local_setup_bindings[id(self.current_test)].add(key)
                    if scope == "suite":
                        self.suite_teardown.add(key)
            elif node_type == "SuiteSetup":
                if scope == "suite":
                    self.suite_setup.add(key)
                self.suite_teardown.add(key)
            elif node_type == "TestSetup":
                default_setup_bindings = (
                    self.default_test_setup_suite if scope == "suite" else self.default_test_setup_local
                )
                default_setup_bindings.add(key)
                if scope == "suite":
                    self.suite_teardown.add(key)
            elif node_type == "TestTeardown" and scope == "suite":
                self.default_test_teardown_suite.add(key)
                self.suite_teardown.add(key)


class AutomaticVariablesChecker(VisitorChecker):
    """Check automatic variable references in contexts known without resolving keyword calls."""

    automatic_variable_not_available: variables.AutomaticVariableNotAvailableRule

    def __init__(self) -> None:
        self.execution_context = "suite context"
        self.suite_bindings: set[VariableKey] = set()
        self.local_bindings: set[VariableKey] = set()
        self.test_setup_bindings: set[VariableKey] = set()
        self.current_test: TestCase | None = None
        self.bindings = AutomaticVariableBindingsCollector()
        super().__init__()

    def visit_File(self, node: Node) -> None:  # noqa: N802
        self.execution_context = "suite context"
        self.bindings = AutomaticVariableBindingsCollector()
        self.bindings.visit(node)
        self.suite_bindings = set(self.bindings.section)
        self.local_bindings = set()
        self.test_setup_bindings = set()
        self.current_test = None
        self.generic_visit(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802, ARG002
        # The caller determines which automatic variables are available in a user keyword.
        return

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        previous_test = self.current_test
        previous_local = self.local_bindings
        previous_setup = self.test_setup_bindings
        self.current_test = node
        self.suite_bindings |= self.bindings.suite_setup | self.bindings.default_test_setup_suite
        self.local_bindings = set(self.bindings.default_test_setup_local)
        self.test_setup_bindings = self.effective_bindings
        self.suite_bindings |= self.bindings.test_setup_suite[id(node)]
        self.local_bindings |= self.bindings.test_setup_local[id(node)]
        self.visit_in_context(node, "test case body")
        self.suite_bindings |= self.bindings.test_teardown_suite[id(node)] | self.bindings.default_test_teardown_suite
        self.local_bindings = previous_local
        self.test_setup_bindings = previous_setup
        self.current_test = previous_test

    def visit_Setup(self, node: Statement) -> None:  # noqa: N802
        self.check_in_context(node, "test setup", self.test_setup_bindings)

    def visit_TestSetup(self, node: Statement) -> None:  # noqa: N802
        bindings = self.bindings.section | self.bindings.suite_setup
        self.check_in_context(node, "test setup", bindings)

    def visit_Teardown(self, node: Statement) -> None:  # noqa: N802
        if self.current_test is None:
            self.check_in_context(node, "test teardown")
            return
        bindings = self.effective_bindings | self.bindings.test[id(self.current_test)]
        self.check_in_context(node, "test teardown", bindings)

    def visit_TestTeardown(self, node: Statement) -> None:  # noqa: N802
        self.check_in_context(node, "test teardown", self.bindings.default_test_teardown)

    def visit_SuiteSetup(self, node: Statement) -> None:  # noqa: N802
        self.check_and_record(node, "suite setup")

    def visit_SuiteTeardown(self, node: Statement) -> None:  # noqa: N802
        self.check_in_context(node, "suite teardown", self.bindings.suite_teardown)

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        self.check_statement(node)
        self.record_bindings(node)

    @property
    def effective_bindings(self) -> set[VariableKey]:
        return self.suite_bindings | self.local_bindings

    def visit_in_context(self, node: Node, context: str) -> None:
        previous_context = self.execution_context
        self.execution_context = context
        self.generic_visit(node)
        self.execution_context = previous_context

    def check_and_record(self, node: Statement, context: str) -> None:
        self.check_in_context(node, context)
        self.record_bindings(node)

    def check_in_context(
        self,
        node: Statement,
        context: str,
        bindings: set[VariableKey] | None = None,
    ) -> None:
        previous_context = self.execution_context
        self.execution_context = context
        self.check_statement(node, bindings)
        self.execution_context = previous_context

    def check_statement(self, node: Statement, bindings: set[VariableKey] | None = None) -> None:
        if bindings is None:
            bindings = self.effective_bindings
        defining_argument = node.get_token(Token.ARGUMENT) if setter_scope(node) is not None else None
        for token in node.data_tokens:
            if token is defining_argument or token.type == Token.VARIABLE:
                continue
            if token.type == Token.ASSIGN and variable_key(token.value) is not None:
                continue
            self.check_token(token, bindings)

    def check_token(self, token: Token, bindings: set[VariableKey]) -> None:
        for variable_match, offset in self.iter_variable_matches(token.value):
            normalized_name = utils.normalize_robot_name(variable_match.base)
            key = (variable_match.identifier, normalized_name)
            variable = f"{variable_match.identifier}{{{variable_match.base}}}"
            self.automatic_variable_not_available.check(
                token=token,
                variable=variable,
                key=key,
                context=self.execution_context,
                offset=offset,
                shadowed=key in bindings,
            )

    def record_bindings(self, node: Statement) -> None:
        for key, scope in statement_bindings(node):
            if scope == "suite":
                self.suite_bindings.add(key)
            elif self.current_test is not None:
                self.local_bindings.add(key)

    @classmethod
    def iter_variable_matches(cls, value: str, offset: int = 0) -> Iterator[tuple[VariableMatch, int]]:
        """Yield top-level and nested variable matches with offsets in the original token."""
        consumed = 0
        for variable_match in VariableMatches(value, ignore_errors=True):
            match_offset = offset + consumed + variable_match.start
            yield variable_match, match_offset
            yield from cls.iter_variable_matches(variable_match.base, match_offset + 2)
            item_start = len(variable_match.identifier) + len(variable_match.base) + 2
            for item in variable_match.items:
                item_start = variable_match.match.find(item, item_start)
                if item_start == -1:
                    continue
                yield from cls.iter_variable_matches(item, match_offset + item_start)
                item_start += len(item)
            consumed += variable_match.end
