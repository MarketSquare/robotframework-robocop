"""
Naming checkers
"""
import re
from collections import defaultdict
from pathlib import Path

from robot.api import Token
from robot.parsing.model.statements import KeywordCall, Arguments

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name, normalize_robot_var_name, IS_RF4, keyword_col, remove_robot_vars


class InvalidCharactersInNameChecker(VisitorChecker):
    """ Checker for invalid characters in suite, test case or keyword name. """
    rules = {
        "0301": (
            "invalid-char-in-name",
            "Invalid character '%s' in %s name",
            RuleSeverity.WARNING,
            (
                'invalid_chars',
                'invalid_chars',
                set,
                'set of characters not allowed in a name'
            )
        )
    }
    var_pattern = re.compile(r'[$@%&]{[^}]+}')

    def __init__(self):
        self.invalid_chars = {'.', '?'}
        self.node_names_map = {
            'KEYWORD_NAME': 'keyword',
            'TESTCASE_NAME': 'test case',
            'SUITE': 'suite'
        }
        super().__init__()

    def visit_File(self, node):
        source = node.source if node.source else self.source
        if source:
            suite_name = Path(source).stem
            if '__init__' in suite_name:
                suite_name = Path(source).parent.name
            self.check_if_char_in_name(node, suite_name, 'SUITE')
        super().visit_File(node)

    def check_if_char_in_node_name(self, node, name_of_node, is_keyword=False):
        if is_keyword:
            matches = [(m.span()) for m in self.var_pattern.finditer(node.name)]
        else:
            matches = []
        index = 0
        while index <= len(node.name):
            index += self._skip_captured_group(index, matches)  # allows to skip ${vars} without breaking indexes
            if index >= len(node.name):
                return
            if node.name[index] in self.invalid_chars:
                self.report("invalid-char-in-name", node.name[index], self.node_names_map[name_of_node],
                            node=node,
                            col=node.col_offset + index + 1)
            index += 1

    @staticmethod
    def _skip_captured_group(index, matches):
        for start, stop in matches:
            if not start < index >= stop:
                return stop - start
        return 0

    def check_if_char_in_name(self, node, name, node_type):
        for char in self.invalid_chars:
            if char in name:
                self.report("invalid-char-in-name", char, self.node_names_map[node_type],
                            node=node)

    def visit_TestCaseName(self, node):  # noqa
        self.check_if_char_in_node_name(node, 'TESTCASE_NAME')

    def visit_KeywordName(self, node):  # noqa
        self.check_if_char_in_node_name(node, 'KEYWORD_NAME', is_keyword=True)


class KeywordNamingChecker(VisitorChecker):
    """ Checker for keyword naming violations. """
    rules = {
        "0302": (
            "wrong-case-in-keyword-name",
            "Keyword name should use title case",
            RuleSeverity.WARNING,
            (
                'convention',
                'convention',
                str,
                "possible values: 'each_word_capitalized' (default) or 'first_word_capitalized'"
            )
        ),
        "0303": (
            "keyword-name-is-reserved-word",
            "'%s' is a reserved keyword%s",
            RuleSeverity.ERROR
        ),
        "0304": (
            "not-enough-whitespace-after-newline-marker",
            "Provide at least two spaces after '...' marker",
            RuleSeverity.ERROR
        ),
        "0305": (
            "underscore-in-keyword-name",
            "Underscores in keyword name can be replaced with spaces",
            RuleSeverity.WARNING
        ),
        "0311": (
            "else-not-upper-case",
            "ELSE and ELSE IF should be upper case",
            RuleSeverity.ERROR
        ),
        "0312": (
            "keyword-name-is-empty",
            "Keyword name should not be empty",
            RuleSeverity.ERROR
        )
    }
    reserved_words = {
        'for': 'for loop',
        'end': 'for loop',
        'while': '',
        'continue': ''
    }
    reserved_words_rf4 = {
        'if': '',
        'for': 'for loop',
        'end': 'for loop or if',
        'while': '',
        'continue': ''
    }
    else_if = {
        'else',
        'else if'
    }

    def __init__(self):
        self.letter_pattern = re.compile(r'\W|_', re.UNICODE)
        self.convention = 'each_word_capitalized'
        super().__init__()

    def visit_SuiteSetup(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_TestSetup(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_Setup(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_SuiteTeardown(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_TestTeardown(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_Teardown(self, node):  # noqa
        self.check_keyword_naming(node.name, node)

    def visit_TestCase(self, node):  # noqa
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name:
            self.report("keyword-name-is-empty", node=node)
        else:
            self.check_keyword_naming(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        self.check_keyword_naming(node.keyword, node)

    def visit_If(self, node):  # noqa
        for keyword in node.body:
            if isinstance(keyword, KeywordCall):
                if keyword.keyword.lower() in self.else_if:
                    self.report("else-not-upper-case", node=keyword, col=keyword_col(keyword))
        self.generic_visit(node)

    def check_keyword_naming(self, keyword_name, node):  # noqa
        if not keyword_name or keyword_name.lstrip().startswith('#'):
            return
        if keyword_name == r'/':  # old for loop, / are interpreted as keywords
            return
        if keyword_name.startswith('...'):
            self.report("not-enough-whitespace-after-newline-marker", node=node)
            return
        if normalize_robot_name(keyword_name) == 'runkeywordif':
            for token in node.data_tokens:
                if (token.value.lower() in self.else_if) and not token.value.isupper():
                    self.report(
                        "keyword-name-is-reserved-word",
                        token.value,
                        self.prepare_reserved_word_rule_message(token.value, 'Run Keyword If'),
                        node=node
                    )
        elif self.check_if_keyword_is_reserved(keyword_name, node):
            return
        keyword_name = remove_robot_vars(keyword_name)
        keyword_name = keyword_name.split('.')[-1]  # remove any imports ie ExternalLib.SubLib.Log -> Log
        keyword_name = keyword_name.replace("'", '')  # replace ' apostrophes
        if '_' in keyword_name:
            self.report("underscore-in-keyword-name", node=node)
        words = self.letter_pattern.sub(' ', keyword_name).split(' ')
        if self.convention == 'first_word_capitalized':
            words = words[:1]
        if any(word[0].islower() for word in words if word):
            self.report("wrong-case-in-keyword-name", node=node)

    def check_if_keyword_is_reserved(self, keyword_name, node):
        # if there is typo in syntax, it is interpreted as keyword
        reserved = self.reserved_words_rf4 if IS_RF4 else self.reserved_words
        if keyword_name.lower() not in reserved:
            return False
        reserved_type = reserved[keyword_name.lower()]
        suffix = self.prepare_reserved_word_rule_message(keyword_name, reserved_type)
        self.report("keyword-name-is-reserved-word", keyword_name, suffix, node=node)
        return True

    @staticmethod
    def prepare_reserved_word_rule_message(name, reserved_type):
        return f". It must be in uppercase ({name.upper()}) when used as a marker with '{reserved_type}'. " \
               f"Each marker should have minimum of 2 spaces as separator." if reserved_type else ''


class SettingsNamingChecker(VisitorChecker):
    """ Checker for settings and sections naming violations. """
    rules = {
        "0306": (
            "setting-name-not-in-title-case",
            "Setting name should be title or upper case",
            RuleSeverity.WARNING
        ),
        "0307": (
            "section-name-invalid",
            "Section name should be in format `*** Capitalized ***` or `*** UPPERCASE ***`",
            RuleSeverity.WARNING
        ),
        "0314": (
            "empty-library-alias",
            "Library alias should not be empty",
            RuleSeverity.ERROR
        ),
        "0315": (
            "duplicated-library-alias",
            "Library alias should not be the same as original name",
            RuleSeverity.WARNING
        )
    }

    def __init__(self):
        self.section_name_pattern = re.compile(r'\*\*\*\s.+\s\*\*\*')
        super().__init__()

    def visit_SectionHeader(self, node):  # noqa
        name = node.data_tokens[0].value
        if not self.section_name_pattern.match(name) or not (name.istitle() or name.isupper()):
            self.report("section-name-invalid", node=node)

    def visit_SuiteSetup(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_TestSetup(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Setup(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Teardown(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_SuiteTeardown(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_TestTeardown(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_ForceTags(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_DefaultTags(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_LibraryImport(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)
        with_name = node.get_token(Token.WITH_NAME)
        if with_name is None:
            for arg in node.get_tokens(Token.ARGUMENT):
                if arg.value and arg.value == 'WITH NAME':
                    self.report("empty-library-alias", node=arg, col=arg.col_offset + 1)
        else:
            if node.alias.replace(' ', '') == node.name.replace(' ', ''):  # New Name == NewName
                name_token = node.get_tokens(Token.NAME)[-1]
                self.report("duplicated-library-alias", node=name_token, col=name_token.col_offset + 1)

    def visit_ResourceImport(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_VariablesImport(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Documentation(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Tags(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Timeout(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Template(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Arguments(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def visit_Return(self, node):  # noqa
        self.check_setting_name(node.data_tokens[0].value, node)

    def check_setting_name(self, name, node):
        if not (name.istitle() or name.isupper()):
            self.report("setting-name-not-in-title-case", node=node)


class TestCaseNamingChecker(VisitorChecker):
    """ Checker for test case naming violations. """
    rules = {
        "0308": (
            "not-capitalized-test-case-title",
            "Test case title should start with capital letter",
            RuleSeverity.WARNING
        ),
        "0313": (
            "test-case-name-is-empty",
            "Test case name should not be empty",
            RuleSeverity.ERROR
        )
    }

    def visit_TestCase(self, node):  # noqa
        if not node.name:
            self.report("test-case-name-is-empty", node=node)
        elif not node.name[0].isupper():
            self.report("not-capitalized-test-case-title", node=node)


class VariableNamingChecker(VisitorChecker):
    """ Checker for variable naming violations. """
    rules = {
        "0309": (
            "section-variable-not-uppercase",
            "Section variable name should be uppercase",
            RuleSeverity.WARNING
        ),
        "0310": (
            "non-local-variables-should-be-uppercase",
            "Test, suite and global variables should be uppercased",
            RuleSeverity.WARNING
        ),
        "0317": (
            "hyphen-in-variable-name",
            "Use underscore in variable names instead of hyphens to avoid treating them like minus sign",
            RuleSeverity.INFO
        )
    }

    def __init__(self):
        self.set_variable_variants = {'settaskvariable',
                                      'settestvariable',
                                      'setsuitevariable',
                                      'setglobalvariable'}
        super().__init__()

    def visit_VariableSection(self, node):  # noqa
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and token.value and not token.value.isupper():
                self.report("section-variable-not-uppercase", lineno=token.lineno,
                            col=token.col_offset)

    def visit_KeywordCall(self, node):  # noqa
        for token in node.get_tokens(Token.ASSIGN):
            if '-' in token.value:
                self.report("hyphen-in-variable-name", lineno=token.lineno, col=token.col_offset)

        if not node.keyword:
            return
        if normalize_robot_name(node.keyword) in self.set_variable_variants:
            if len(node.data_tokens) < 2:
                return
            token = node.data_tokens[1]
            if token.type == Token.ARGUMENT and not token.value.isupper():
                self.report("non-local-variables-should-be-uppercase", node=node, col=token.col_offset + 1)


class SimilarVariableChecker(VisitorChecker):
    """ Checker for finding same variables with similar names. """
    rules = {
        "0316": (
            "possible-variable-overwriting",
            "Variable '%s' may overwrite similar variable inside '%s' %s. "
            "Note that variables are case-insensitive, and also spaces and underscores are ignored.",
            RuleSeverity.INFO
        )
    }

    def __init__(self):
        self.variables = defaultdict(set)
        self.parent_name = ''
        self.parent_type = ''
        super().__init__()

    def visit_Keyword(self, node):  # noqa
        self.variables = defaultdict(set)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        self.visit_vars_and_find_similar(node)
        self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa
        self.variables = defaultdict(set)
        self.parent_name = node.name
        self.parent_type = type(node).__name__
        self.visit_vars_and_find_similar(node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        tokens = node.get_tokens(Token.ASSIGN)
        self.find_similar_variables(tokens, node)

    def visit_For(self, node):  # noqa
        for var in node.variables:
            self.variables[normalize_robot_var_name(var)].add(var)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        for var in node.variables:
            self.variables[normalize_robot_var_name(var)].add(var)
        self.generic_visit(node)

    def visit_vars_and_find_similar(self, node):
        """
        Creates a dictionary `variables` with normalized variable name as a key
        and ads a list of all detected variations of this variable in the node as a value,
        then it checks if similar variable was found.
        """
        for child in node.body:
            # read arguments from Test Case or Keyword
            if isinstance(child, Arguments):
                for token in child.get_tokens(Token.ARGUMENT):
                    self.variables[normalize_robot_var_name(token.value)].add(token.value)

    def find_similar_variables(self, tokens, node):
        for token in tokens:
            normalized_token = normalize_robot_var_name(token.value)
            if normalized_token in self.variables and token.value not in self.variables[normalized_token]:
                self.report("possible-variable-overwriting", token.value, self.parent_name, self.parent_type,
                            node=node, lineno=token.lineno, col=token.col_offset)
            self.variables[normalized_token].add(token.value)
