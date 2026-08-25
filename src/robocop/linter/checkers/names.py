"""Checker for rules triggered by keyword, variable and argument names."""

from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.variables.search import search_variable

from robocop.linter.rules import VisitorChecker, naming, variables
from robocop.linter.utils import misc as utils
from robocop.parsing.run_keywords import iterate_keyword_names

if TYPE_CHECKING:
    from robot.parsing.model.blocks import If, Keyword
    from robot.parsing.model.statements import Arguments, KeywordCall, Node, Setup, Template, Var, Variable


class NamesChecker(VisitorChecker):
    """
    Checker for rules reported for the names of keywords, variables and arguments.

    Keyword names are checked wherever a keyword can be referenced (definitions, calls, setups, teardowns and
    templates), and variable names wherever a variable can be assigned.
    """

    wrong_case_in_keyword_name: naming.WrongCaseInKeywordNameRule
    wrong_case_in_keyword_call: naming.WrongCaseInKeywordCallRule
    keyword_name_is_reserved_word: naming.KeywordNameIsReservedWordRule
    underscore_in_keyword_name: naming.UnderscoreInKeywordNameRule
    else_not_upper_case: naming.ElseNotUpperCaseRule
    keyword_name_is_empty: naming.KeywordNameIsEmptyRule
    bdd_without_keyword_call: naming.BddWithoutKeywordCallRule
    section_variable_not_uppercase: naming.SectionVariableNotUppercaseRule
    non_local_variables_should_be_uppercase: variables.NonLocalVariablesShouldBeUppercaseRule
    hyphen_in_variable_name: variables.HyphenInVariableNameRule
    overwriting_reserved_variable: variables.OverwritingReservedVariableRule

    def __init__(self) -> None:
        self.inside_if_block = False
        super().__init__()

    def visit_File(self, node: Node) -> None:  # noqa: N802
        self.inside_if_block = False
        self.generic_visit(node)

    def visit_Keyword(self, node: Keyword) -> None:  # noqa: N802
        self.keyword_name_is_empty.check(node)
        if node.name:
            self.check_keyword_naming(node.name, node, is_keyword_definition=True)
        self.parse_embedded_arguments(node.header.get_token(Token.KEYWORD_NAME))
        self.generic_visit(node)

    def visit_Setup(self, node: Setup) -> None:  # noqa: N802
        self.bdd_without_keyword_call.check(node.name, node)
        self.check_keyword_naming_with_subkeywords(node, Token.NAME)

    visit_TestTeardown = visit_SuiteTeardown = visit_Teardown = visit_TestSetup = visit_SuiteSetup = visit_Setup  # noqa: N815

    def visit_Template(self, node: Template) -> None:  # noqa: N802
        if node.value:
            self.check_keyword_naming(node.value, node.get_token(Token.NAME))
        self.generic_visit(node)

    visit_TestTemplate = visit_Template  # noqa: N815

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        if self.inside_if_block:
            self.else_not_upper_case.check(node)
        self.check_keyword_naming_with_subkeywords(node, Token.KEYWORD)
        self.bdd_without_keyword_call.check(node.keyword, node)
        for token in node.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable")
        self.check_set_variable_keyword(node)

    def visit_If(self, node: If) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ASSIGN):
            self.check_for_reserved_naming_or_hyphen(token, "Variable")
        self.inside_if_block = True
        self.generic_visit(node)
        self.inside_if_block = False

    def visit_Variable(self, node: Variable) -> None:  # noqa: N802
        token = node.data_tokens[0]
        try:
            var_name = search_variable(token.value).base
        except VariableError:
            return  # TODO: Ignore for now, for example ${not  closed in variables will throw it
        if var_name is None:
            return  # in RF<=5, a continuation mark ` ...` is wrongly considered a variable
        self.section_variable_not_uppercase.check(token, utils.remove_variable_type_conversion(var_name))
        self.check_for_reserved_naming_or_hyphen(token, "Variable")

    def visit_Var(self, node: Var) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        variable = node.get_token(Token.VARIABLE)
        if not variable:
            return
        self.check_for_reserved_naming_or_hyphen(variable, "Variable")
        # TODO: Check supported syntax for variable, ie ${{var}}?
        if not utils.is_var_scope_local(node):
            self.non_local_variables_should_be_uppercase.check(search_variable(variable.value).base, node, variable)

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        for arg in node.get_tokens(Token.ARGUMENT):
            self.check_for_reserved_naming_or_hyphen(arg, "Argument")

    def check_keyword_naming_with_subkeywords(self, node: Setup | KeywordCall, name_token_type: str) -> None:
        for keyword in iterate_keyword_names(node, name_token_type):
            self.check_keyword_naming(keyword.value, keyword)

    def check_keyword_naming(self, keyword_name: str, node: Node, is_keyword_definition: bool = False) -> None:
        if not keyword_name or keyword_name.lstrip().startswith("#"):
            return
        if keyword_name == r"/":  # old for loop, / are interpreted as keywords
            return
        if self.keyword_name_is_reserved_word.check(node, keyword_name, self.inside_if_block):
            return
        case_naming_rule: naming.WrongCaseInKeywordNameRule | naming.WrongCaseInKeywordCallRule
        if is_keyword_definition:
            case_naming_rule = self.wrong_case_in_keyword_name
        else:
            case_naming_rule = self.wrong_case_in_keyword_call
        normalized = naming.normalize_keyword_name(keyword_name, case_naming_rule.pattern, is_keyword_definition)
        self.underscore_in_keyword_name.check(node, keyword_name, normalized)
        case_naming_rule.check(node, keyword_name, normalized)

    def check_set_variable_keyword(self, node: KeywordCall) -> None:
        """Check the name of a variable assigned with one of the ``Set * Variable`` keywords."""
        if not node.keyword:
            return
        if utils.normalize_robot_name(node.keyword, remove_prefix="builtin.") not in naming.SET_VARIABLE_VARIANTS:
            return
        if len(node.data_tokens) < 2:
            return
        token = node.data_tokens[1]
        if not token.value:
            return
        try:
            var_name = search_variable(token.value).base
        except VariableError:
            return  # TODO: Ignore for now, for example ${not  closed in variables will throw it
        if var_name is None:  # possibly $escaped or \${escaped}, or invalid variable name
            return
        self.non_local_variables_should_be_uppercase.check(var_name, node, token)

    def parse_embedded_arguments(self, name_token: Token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns like (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    self.check_for_reserved_naming_or_hyphen(token, "Embedded argument", has_pattern=True)
        except VariableError:
            pass

    def check_for_reserved_naming_or_hyphen(self, token: Token, var_or_arg: str, has_pattern: bool = False) -> None:
        """Check if variable name is a reserved Robot Framework name or uses hyphen in the name."""
        variable_match = search_variable(token.value, ignore_errors=True)
        name = variable_match.base
        if has_pattern:
            name, *_ = name.split(":", maxsplit=1)  # var:pattern -> var
        if not name:
            return
        self.hyphen_in_variable_name.check(token, name)
        self.overwriting_reserved_variable.check(token, variable_match, name, var_or_arg)
