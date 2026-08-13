"""Checkers for the rules defined in ``robocop.linter.rules.misc``."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.statements import Arguments, KeywordCall, Teardown
from robot.variables.search import search_variable

from robocop.linter.rules import AfterRunChecker, Rule, VisitorChecker, arguments, misc, variables
from robocop.linter.rules.misc import CachedVariable, SectionVariablesCollector
from robocop.linter.utils import misc as utils
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from collections.abc import Generator

    from robot.parsing.model import File, Keyword, TestCase
    from robot.parsing.model.blocks import For, If, TestCaseSection, Try, While
    from robot.parsing.model.statements import LibraryImport, Node

    from robocop.linter.diagnostics import Diagnostic
    from robocop.linter.utils.disablers import DisablersFinder
    from robocop.source_file import SourceFile


class UnusedVariablesChecker(VisitorChecker):
    unused_argument: arguments.UnusedArgumentRule
    unused_variable: variables.UnusedVariableRule
    argument_overwritten_before_usage: arguments.ArgumentOverwrittenBeforeUsageRule
    variable_overwritten_before_usage: variables.VariableOverwrittenBeforeUsageRule

    _VARIABLE_START = set("$@&%")
    _VARIABLE_START_PATTERN = re.compile(r"[$@&%]\{")
    _ESCAPED_VAR_PATTERN = re.compile(r"\$([A-Za-z_]\w*)")
    _VARIABLE_NAME_PATTERN = re.compile(r"\w+")

    def __init__(self) -> None:
        self.arguments: dict[str, CachedVariable] = {}
        self.variables: list[dict[str, CachedVariable]] = [
            {}
        ]  # variables are list of scope-dictionaries, to support IF branches
        self.current_if_variables: list[dict[str, CachedVariable]] = []
        self.section_variables: dict[str, CachedVariable] = {}
        self.used_in_scope: list[set[str]] = []  # variables that were used in current FOR/WHILE loop
        self.ignore_overwriting = False  # temporarily ignore overwriting, e.g. in FOR loops
        self.in_loop = False  # if we're in the loop we need to check whole scope for unused-variable
        self.test_or_task_section = False
        self.branch_level = 0  # if we're inside any if branch, it will be > 0
        # Local [Teardown] nodes deferred to be processed after the rest of test/keyword body,
        # so variables assigned later in the body are visible to the teardown (issue #1607).
        self.deferred_teardowns: list[Teardown] = []
        super().__init__()

    def visit_File(self, node: File) -> None:  # noqa: N802
        self.test_or_task_section = False
        section_variables = SectionVariablesCollector()
        section_variables.visit(node)
        self.section_variables = section_variables.section_variables
        self.generic_visit(node)
        self.report_not_used_section_variables()

    def report_not_used_section_variables(self) -> None:
        if not self.test_or_task_section:
            return
        ignored = self.get_ignored_variable_names()
        for variable in self.section_variables.values():
            should_ignore = variable.is_used or utils.normalize_robot_var_name(variable.name) in ignored
            if not should_ignore:
                self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)

    def get_ignored_variable_names(self) -> set[str]:
        """Get normalized set of variable names to ignore from the ignore parameter."""
        ignore_config = self.unused_variable.ignore
        if not ignore_config:
            return set()
        return {utils.normalize_robot_name(name.strip()) for name in ignore_config.split(",")}

    def visit_TestCaseSection(self, node: TestCaseSection) -> None:  # noqa: N802
        self.test_or_task_section = True
        self.generic_visit(node)

    visit_TaskSection = visit_TestCaseSection  # noqa: N815

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.variables = [{}]
        previous_deferred = self.deferred_teardowns
        self.deferred_teardowns = []
        self.generic_visit(node)
        self.process_deferred_teardowns()
        self.deferred_teardowns = previous_deferred
        self.check_unused_variables()

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.arguments = {}
        self.variables = [{}]
        previous_deferred = self.deferred_teardowns
        self.deferred_teardowns = []
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        # iterating there instead of using visit_Arguments, so we don't check keywords without arguments
        for statement in node.body:
            if isinstance(statement, Arguments):
                self.parse_arguments(statement)
        self.generic_visit(node)
        self.process_deferred_teardowns()
        self.deferred_teardowns = previous_deferred
        for arg in self.arguments.values():
            if not arg.is_used:
                value, *_ = arg.token.value.split("=", maxsplit=1)
                self.report_arg_or_var_rule(self.unused_argument, arg.token, value)
        self.check_unused_variables()
        self.arguments = {}

    def visit_Teardown(self, node: Teardown) -> None:  # noqa: N802
        # Defer processing of local [Teardown] until after the rest of the test/keyword body has
        # been visited, so variables assigned later in the body are also marked as used.
        self.deferred_teardowns.append(node)

    def process_deferred_teardowns(self) -> None:
        for node in self.deferred_teardowns:
            for token in node.get_tokens(Token.NAME, Token.ARGUMENT):
                self.find_not_nested_variable(token.value, can_be_escaped=False)

    def check_unused_variables(self) -> None:
        for scope in self.variables:
            self.check_unused_variables_in_scope(scope)

    def check_unused_variables_in_scope(self, scope: dict[str, CachedVariable]) -> None:
        for variable in scope.values():
            if not variable.is_used:
                self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)

    def report_arg_or_var_rule(self, rule: Rule, token: Token, value: str | None = None) -> None:
        if value is None:
            value = token.value
        self.report(
            rule,
            name=value,
            node=token,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.col_offset + len(value) + 1,
        )

    def add_argument(self, argument: str, normalized_name: str, token: Token) -> None:
        self.arguments[normalized_name] = CachedVariable(argument, token, is_used=False)

    def parse_arguments(self, node: Arguments) -> None:
        """Store arguments from [Arguments]. Ignore @{args} and &{kwargs}, strip default values."""
        if node.errors:
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            if arg.value[0] in ("@", "&"):  # ignore *args and &kwargs
                continue
            arg_name, default_value = utils.split_argument_default_value(arg.value)
            if default_value:
                self.find_not_nested_variable(default_value, can_be_escaped=False)
            base_name = arg_name[2:-1]
            name = utils.remove_variable_type_conversion(base_name)
            name = utils.normalize_robot_name(name)
            self.add_argument(base_name, name, token=arg)
            # ${test.kws[0].msgs[${index}]} FIXME

    def parse_embedded_arguments(self, name_token: Token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        if "$" not in name_token.value:
            return
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    normalized_name = utils.normalize_robot_var_name(token.value)
                    name, *_ = normalized_name.split(":", maxsplit=1)
                    self.add_argument(token.value, name, token=token)
        except VariableError:
            pass

    def visit_If(self, node: If) -> None:  # noqa: N802
        if node.header.errors:
            return
        self.branch_level += 1
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.variables.append({})
        for item in node.body:
            self.visit(item)
        if_variables = self.variables.pop()
        if node.orelse:
            self.visit_IfBranch(node.orelse)
        for token in node.header.get_tokens(Token.ASSIGN):
            self.handle_assign_variable(token)
        self.branch_level -= 1
        for scope in self.current_if_variables:
            for name, variable in scope.items():
                if name in if_variables:
                    if_variables[name].is_used = if_variables[name].is_used and variable.is_used
                    if not variable.is_used:
                        if_variables[name].token = variable.token
                else:
                    if_variables[name] = variable
        self.add_variables_from_if_to_scope(if_variables)
        self.current_if_variables = []

    def visit_IfBranch(self, node: Node) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.variables.append({})
        for child in node.body:
            self.visit(child)
        self.current_if_variables.append(self.variables.pop())
        if node.orelse:
            self.visit_IfBranch(node.orelse)

    def add_variables_from_if_to_scope(self, if_variables: dict[str, CachedVariable]) -> None:
        """
        Add all variables in the given IF branch to a common scope.

        If a variable is used already in the branch, it will also be marked as used.
        """
        if not self.variables:
            self.variables.append(if_variables)
            return
        for var_name, cached_var in if_variables.items():
            if var_name in self.variables[-1]:
                if cached_var.is_used:
                    self.variables[-1][var_name].is_used = True
            else:
                self.variables[-1][var_name] = cached_var

    def visit_LibraryImport(self, node: LibraryImport) -> None:  # noqa: N802
        for token in node.get_tokens(Token.NAME, Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=False)

    visit_TestTags = visit_ForceTags = visit_Metadata = visit_DefaultTags = (  # noqa: N815
        visit_Variable  # noqa: N815
    ) = visit_ReturnStatement = visit_ReturnSetting = (  # noqa: N815
        visit_Timeout  # noqa: N815
    ) = visit_Return = visit_SuiteSetup = (  # noqa: N815  # noqa: N815
        visit_SuiteTeardown  # noqa: N815
    ) = visit_TestSetup = visit_TestTeardown = visit_Setup = (  # noqa: N815
        visit_ResourceImport  # noqa: N815
    ) = visit_VariablesImport = visit_Tags = (  # noqa: N815  # noqa: N815
        visit_Documentation  # noqa: N815
    ) = visit_LibraryImport

    def clear_variables_after_loop(self) -> None:
        """Remove used variables after the loop finishes."""
        for index, scope in enumerate(self.variables):
            self.variables[index] = {name: variable for name, variable in scope.items() if not variable.is_used}

    def revisit_variables_used_in_loop(self) -> None:
        """
        Revisit the variables used in the loop.

        Due to the recursive nature of the loops, we need to revisit variables used in the loop again in case
        the variable defined in the further part of the loop was used.

        In case of nested FOR/WHILE loops, we're storing variables in separate stacks that are merged until we reach
        the outer END.

        For example:

            *** Keywords ***
            Use loop variable
                WHILE    ${True}
                    ${counter}    Update Counter    ${counter}
                END
        """
        # TODO: Instead of revisiting, we could mark all variables added in loop as used
        top_stack = self.used_in_scope.pop()
        if self.used_in_scope:
            self.used_in_scope[-1] = self.used_in_scope[-1].union(top_stack)
        else:
            for name in top_stack:
                self._set_variable_as_used(name, self.variables[-1])

    def visit_While(self, node: While) -> None:  # noqa: N802
        if node.header.errors:
            return
        self.in_loop = True
        self.used_in_scope.append(set())
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        if node.limit:
            self.find_not_nested_variable(node.limit, can_be_escaped=False)
        self.generic_visit(node)
        self.in_loop = False
        self.revisit_variables_used_in_loop()
        self.clear_variables_after_loop()

    def visit_For(self, node: For) -> None:  # noqa: N802
        if getattr(node.header, "errors", None):
            return
        self.in_loop = True
        self.used_in_scope.append(set())
        self.ignore_overwriting = True
        for token in node.header.get_tokens(Token.ARGUMENT, "OPTION"):  # Token.Option does not exist for RF3 and RF4
            self.find_not_nested_variable(token.value, can_be_escaped=False)
        for token in node.header.get_tokens(Token.VARIABLE):
            self.handle_assign_variable(token)
        self.generic_visit(node)
        self.ignore_overwriting = False
        self.in_loop = False
        self.revisit_variables_used_in_loop()
        self.clear_variables_after_loop()

    visit_ForLoop = visit_For  # noqa: N815

    @staticmethod
    def try_assign(try_node: Node) -> str | None:
        if ROBOT_VERSION.major < 7:
            return try_node.variable  # type: ignore[no-any-return]
        return try_node.assign  # type: ignore[no-any-return]

    def visit_Try(self, node: Try) -> None:  # noqa: N802
        if node.errors or node.header.errors:
            return
        # first gather variables from the TRY node
        self.variables.append({})
        for item in node.body:
            self.visit(item)
        try_variables = self.variables.pop()
        branch_variables = []
        try_branch = node.next
        while try_branch:
            self.variables.append({})
            # variables in EXCEPT  ${error_pattern}
            for token in try_branch.header.get_tokens(Token.ARGUMENT, Token.OPTION):
                self.find_not_nested_variable(token.value, can_be_escaped=True)
            # except AS ${err}
            if self.try_assign(try_branch) is not None:
                error_var = try_branch.header.get_token(Token.VARIABLE)
                if error_var is not None:
                    self.handle_assign_variable(error_var, ignore_var_conversion=False)
                    for variable in self.variables[-1].values():
                        variable.current_scopy_only = True
            # visit body of branch
            for item in try_branch.body:
                self.visit(item)
            branch_variables.append(self.variables.pop())
            try_branch = try_branch.next
        for branch in branch_variables:
            for name, variable in branch.items():
                if variable.current_scopy_only:
                    if not variable.is_used:
                        self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)
                elif name not in try_variables:
                    try_variables[name] = variable
                else:
                    try_variables[name].is_used = try_variables[name].is_used and variable.is_used
                    if not variable.is_used:
                        try_variables[name].token = variable.token
        self.add_variables_from_if_to_scope(try_variables)

    def visit_Group(self, node: Node) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.generic_visit(node)

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        for token in node.get_tokens(Token.KEYWORD):  # argument can be used in the keyword name
            self.find_not_nested_variable(token.value, can_be_escaped=False)
        for token in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        for token in node.get_tokens(Token.ASSIGN):  # we first check args, then assign for used and then overwritten
            self.handle_assign_variable(token)

    def visit_Var(self, node: Node) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg.value, can_be_escaped=True)
        variable = node.get_token(Token.VARIABLE)
        if variable and utils.is_var_scope_local(node):
            self.handle_assign_variable(variable)

    def visit_TemplateArguments(self, node: Node) -> None:  # noqa: N802
        for argument in node.data_tokens:
            self.find_not_nested_variable(argument.value, can_be_escaped=False)

    def handle_assign_variable(self, token: Token, ignore_var_conversion: bool = True) -> None:
        """
        Check if assign does not overwrite arguments or variables.

        Store assign variables for future overwriting checks.
        """
        value = token.value
        variable_match = search_variable(value, ignore_errors=True)
        name = variable_match.base
        if ignore_var_conversion:
            name = utils.remove_variable_type_conversion(name)
        normalized = utils.normalize_robot_name(name)
        if not normalized or name.startswith("_"):  # i.e. "${_}" -> "", or ${_ignore}
            return
        arg = self.arguments.get(normalized, None)
        if arg is not None:
            if not arg.is_used and self.branch_level == 0:
                self.report_arg_or_var_rule(self.argument_overwritten_before_usage, arg.token)
            arg.is_used = is_used = True
        else:
            is_used = False
        if not variable_match.items:  # not item assignment like ${var}[1] =
            variable_scope = self.variables[-1]
            if normalized in variable_scope:
                is_used = variable_scope[normalized].is_used
                if not is_used and not self.ignore_overwriting:
                    self.report_arg_or_var_rule(
                        self.variable_overwritten_before_usage,
                        variable_scope[normalized].token,
                        variable_scope[normalized].name,
                    )
            else:  # check for attribute access like .lower() or .x
                for variable_scope in self.variables[::-1]:
                    base_name = self.search_by_tokenize(normalized, variable_scope)
                    if base_name:
                        variable_scope[base_name[0]].is_used = True
                        self.variables[-1][normalized] = CachedVariable(variable_match.name, token, is_used=True)
                        return
        if self.in_loop:
            variable = CachedVariable(variable_match.name, token, is_used)
        else:
            variable = CachedVariable(variable_match.name, token, is_used=False)
        self.variables[-1][normalized] = variable

    def find_not_nested_variable(self, value: str, can_be_escaped: bool) -> None:
        r"""
        Find and process not nested variable.

        Examples:
            '${value}' -> value
            ${value_${nested}} -> nested
            'String with ${var} and $escaped' -> var, escaped

        Found variables are added to the scope.

        """
        full_match = False  # whether string is a variable only

        # Find all starting positions
        for match in self._VARIABLE_START_PATTERN.finditer(value):
            start_pos = match.start()
            # Now find the matching closing brace
            depth = 0
            for i in range(start_pos, len(value)):
                if value[i] == "{" and i > 0 and value[i - 1] in self._VARIABLE_START:
                    depth += 1
                elif value[i] == "}":
                    depth -= 1
                    if depth == 0:
                        self.update_used_variables(value[start_pos + 2 : i])
                        full_match = start_pos == 0 and i + 1 == len(value)
                        break

        # no need to search further if we matched fully ('${var}')
        if not can_be_escaped or full_match:
            return
        self.find_escaped_variables(value)

    def find_escaped_variables(self, value: str) -> None:
        """Find all $var escaped variables in the value string and process them."""
        # TODO: create iter_escaped_variables function
        if "$" not in value:
            return
        for match in self._ESCAPED_VAR_PATTERN.finditer(value):
            variable_name = match.group(1)
            if variable_name.isidentifier():
                self.update_used_variables(variable_name)

    def update_used_variables(self, variable_name: str) -> None:
        """
        Remove used variable from the arguments and variables store.

        If the normalized variable name was already defined, we need to remove it to know which variables are not used.
        If the variable is not found, we try to remove possible attribute access from the name and search again.
        For example:

          arg.attr -> arg
          arg["value"] -> arg
        """
        normalized = utils.normalize_robot_name(variable_name)
        if self.used_in_scope:
            self.used_in_scope[-1].add(normalized)
        for variable_scope in self.variable_namespaces():
            self._set_variable_as_used(normalized, variable_scope)

    def variable_namespaces(self) -> Generator[dict[str, CachedVariable], None, None]:
        yield self.arguments
        yield self.section_variables
        yield from self.variables[::-1]

    def _set_variable_as_used(self, normalized_name: str, variable_scope: dict[str, CachedVariable]) -> None:
        """If variable is found in variable_scope, set it as used."""
        if normalized_name in variable_scope:
            variable_scope[normalized_name].is_used = True
        else:
            self.search_by_tokenize(normalized_name, variable_scope)

    def search_by_tokenize(self, variable_name: str, variable_scope: dict[str, CachedVariable]) -> list[str]:
        """Search variables in string by tokenizing variable name using Python ast."""
        if not variable_scope:
            return []
        # there is no syntax like ${var * 2}
        if self._VARIABLE_NAME_PATTERN.fullmatch(variable_name):
            if variable_name in variable_scope:
                variable_scope[variable_name].is_used = True
                return [variable_name]
            return []
        found = []
        for name in utils.get_variables_from_string(variable_name):
            if name in variable_scope:
                variable_scope[name].is_used = True
                found.append(name)
        return found


class UnusedDiagnosticChecker(AfterRunChecker):
    unused_disabler: misc.DisablerNotUsedRule

    def scan_file(self, source_file: SourceFile, **kwargs: object) -> list[Diagnostic]:
        disablers: DisablersFinder = kwargs["disablers"]  # type: ignore[assignment]
        super().scan_file(source_file, **kwargs)
        self.check_unused_disablers(disablers)
        return self.issues

    def check_unused_disablers(self, disablers: DisablersFinder) -> None:
        for rule, disabler in disablers.not_used_disablers:
            self.report(
                self.unused_disabler,
                rule_name=rule,
                lineno=disabler.start_line,
                end_lineno=disabler.start_line,
                col=disabler.directive_col_start,
                end_col=disabler.directive_col_end,
            )
