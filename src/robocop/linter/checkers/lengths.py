"""Checkers for the rules defined in ``robocop.linter.rules.lengths``."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.blocks import Keyword, TestCase
from robot.variables.search import search_variable

from robocop.linter.rules import VisitorChecker, lengths
from robocop.linter.rules.lengths import CachedVariable
from robocop.linter.utils.misc import (
    find_escaped_variables,
    normalize_robot_name,
    split_argument_default_value,
    strip_equals_from_assignment,
)
from robocop.version_handling import TYPE_SUPPORTED

if TYPE_CHECKING:
    from robot.parsing.model.blocks import For, Try, VariableSection
    from robot.parsing.model.statements import Arguments, KeywordCall, Node, Statement


class VariableNameLengthChecker(VisitorChecker):
    """Checker for max length variable names."""

    too_long_variable_name: lengths.TooLongVariableNameRule

    set_variable_keywords = {
        "setlocalvariable",
        "settestvariable",
        "settaskvariable",
        "setsuitevariable",
        "setglobalvariable",
    }

    def __init__(self) -> None:
        super().__init__()
        self.variables: dict[str, CachedVariable] = {}
        self.var_identifiers = "$@&"

    def visit_Node(self, node: Node) -> None:  # noqa: N802
        if not node.errors:
            self.generic_visit(node)

    def new_variable_scope(self, node: Keyword | TestCase | VariableSection) -> None:
        """Handle new scope by resetting list of known variables."""
        self.variables.clear()
        if isinstance(node, Keyword):
            self.parse_embedded_arguments(node.header.get_token(Token.KEYWORD_NAME))
        self.generic_visit(node)
        self.check_variable_names_and_report()

    visit_TestCase = visit_VariableSection = visit_Keyword = new_variable_scope  # noqa: N815

    def parse_embedded_arguments(self, name_token: Token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    self.add_variable_to_scope(token, has_pattern=True)
        except VariableError:
            pass

    def add_variable_to_scope(self, node: Statement, var_name: str | None = None, has_pattern: bool = False) -> None:
        """
        Add the variable to the known variables.

        Determine name of variable by stripping item accessors and type conversions
        and add it to known variables if not already present.
        """
        end_col_offset = 1
        if getattr(node, "errors", None) or getattr(node, "error", None):
            return
        if not var_name:
            var_name = node.name if hasattr(node, "name") else node.value
        # Escaped variable name handling : \${var}
        # Using robot.utils.unescape(var_name) does not only unescape start of name
        escaped_var, var_name = var_name.startswith("\\"), var_name.lstrip("\\")
        if escaped_var:
            end_col_offset += 1  # leading backslash
        # Strip all item and possible type conversions : ${list}[0] , ${var: int}
        try:
            search = search_variable(var_name, parse_type=True) if TYPE_SUPPORTED else search_variable(var_name)  # pylint: disable=unexpected-keyword-arg
        except VariableError:  # Incomplete data, e.g. `${arg`
            return
        # Handle var name without brackets passed to Set Local/Global/Suite/Test Variable : $var
        # And escaped sytnax containing unescaped variables $var_${var2}
        if search.base and not find_escaped_variables(var_name):
            name = search.base
            # The reason for moving this here is the search_variable("$var_@{var2}[0]_something").items is ['0'] :
            # Dynamic variable names are insane
            for i in search.items:
                end_col_offset -= len(i) + 2  # highlight variable only, not item accessors
        else:
            name = search.string.lstrip(self.var_identifiers)
        # Item assignment using extended variable syntax : ${dict.key}
        # dynamic variable name with extended syntax like ${var_${var2.key}} :
        if not any(i in name for i in self.var_identifiers):
            name, *_ = name.split(".", maxsplit=1)  # re.split(r"(?<!\\)\.", name, maxsplit=1)  # unescaped dots only
        # Strip pattern from variable name
        if has_pattern:
            name, *_ = name.split(":", maxsplit=1)  # re.split(r"(?<!\\):", name, 1)  # unescaped colon only
        # Finally cache variable in current scope for checking, if not already present
        if (norm_name := normalize_robot_name(name)) not in self.variables:
            if len(var_name) + end_col_offset <= 0:
                return  # sanity check
            self.variables[norm_name] = CachedVariable(name, node, len(var_name) + end_col_offset)

    def check_variable_names_and_report(self) -> None:
        for var in self.variables.values():
            if (length := len(var.name)) > self.too_long_variable_name.max_len:
                self.report(
                    self.too_long_variable_name,
                    variable_name=var.name,
                    variable_name_length=length,
                    allowed_length=self.too_long_variable_name.max_len,
                    node=var.node,
                    end_col=var.node.col_offset + var.end_col,
                    sev_threshold_value=length,
                )

    visit_Variable = add_variable_to_scope  # noqa: N815

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if not node.keyword:
            return
        for variable in node.get_tokens(Token.ASSIGN):
            self.add_variable_to_scope(variable, strip_equals_from_assignment(variable.value))
        # Only check args of 'Set ... Variable' and check for invalid RF syntax
        if (
            normalize_robot_name(node.keyword) in self.set_variable_keywords
            and (argument := node.get_token(Token.ARGUMENT))
            and argument.value.startswith(tuple(self.var_identifiers + "\\"))
        ):
            self.add_variable_to_scope(argument)

    def visit_Var(self, node: Statement) -> None:  # noqa: N802
        if variable := node.get_token(Token.VARIABLE):
            self.add_variable_to_scope(variable, strip_equals_from_assignment(variable.value))

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        for argument in node.get_tokens(Token.ARGUMENT):
            name, _ = split_argument_default_value(argument.value)
            self.add_variable_to_scope(argument, name)

    def visit_For(self, node: For) -> None:  # noqa: N802
        if node.header.errors:
            return
        for variable in node.header.get_tokens(Token.VARIABLE):
            self.add_variable_to_scope(variable)
        self.generic_visit(node)  # continue to nested loops

    def visit_Try(self, node: Try) -> None:  # noqa: N802
        if (node.type is Token.EXCEPT) and (variable := node.header.get_token(Token.VARIABLE)):
            self.add_variable_to_scope(variable)
        self.generic_visit(node)  # continue to all branches
