"""
Naming checkers
"""
import re
from pathlib import Path
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name

from robot.api import Token


class InvalidCharactersInNameChecker(VisitorChecker):
    """ Checker for invalid characters in suite, test case or keyword name. """
    rules = {
        "0301": (
            "invalid-char-in-name",
            "Invalid character %s in %s name",
            RuleSeverity.WARNING,
            ('invalid_chars', 'invalid_chars', set)
        )
    }

    def __init__(self, *args):
        self.invalid_chars = ('.', '?')
        self.node_names_map = {
            'KEYWORD_NAME': 'keyword',
            'TESTCASE_NAME': 'test case',
            'SUITE': 'suite'
        }
        super().__init__(*args)

    def visit_File(self, node):
        suite_name = Path(node.source).stem
        if '__init__' in suite_name:
            suite_name = Path(node.source).parent.name
        self.check_if_char_in_name(node, suite_name, 'SUITE')
        super().visit_File(node)

    def check_if_char_in_node_name(self, node, name_of_node):
        for index, char in enumerate(node.name):
            if char in self.invalid_chars:
                self.report("invalid-char-in-name", char, self.node_names_map[name_of_node],
                            node=node,
                            col=node.col_offset + index + 1)

    def check_if_char_in_name(self, node, name, node_type):
        for char in self.invalid_chars:
            if char in name:
                self.report("invalid-char-in-name", char, self.node_names_map[node_type],
                            node=node)

    def visit_TestCaseName(self, node):  # noqa
        self.check_if_char_in_node_name(node, 'TESTCASE_NAME')

    def visit_KeywordName(self, node):  # noqa
        self.check_if_char_in_node_name(node, 'KEYWORD_NAME')


class KeywordNamingChecker(VisitorChecker):
    """ Checker for keyword naming violations. """
    rules = {
        "0302": (
            "not-capitalized-keyword-name",
            "Keyword name should be capitalized",
            RuleSeverity.WARNING
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
        )
    }
    reserved_words = {
        'for': 'for loop',
        'end': 'for loop',
        'while': '',
        'continue': ''
    }
    else_if = {
        'else',
        'else if'
    }

    def __init__(self, *args):
        self.letter_pattern = re.compile('[^a-zA-Z0-9]')
        self.var_pattern = re.compile(r'[$@%&]{.+}')
        super().__init__(*args)

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
        self.check_keyword_naming(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        self.check_keyword_naming(node.keyword, node)

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
        keyword_name = keyword_name.split('.')[-1]  # remove any imports ie ExternalLib.SubLib.Log -> Log
        keyword_name = self.var_pattern.sub('', keyword_name)  # remove any embedded variables from name
        keyword_name = keyword_name.replace("'", '')  # replace ' apostrophes
        if '_' in keyword_name:
            self.report("underscore-in-keyword-name", node=node)
        words = self.letter_pattern.sub(' ', keyword_name).split(' ')
        if any(word[0].islower() for word in words if word):
            self.report("not-capitalized-keyword-name", node=node)

    def check_if_keyword_is_reserved(self, keyword_name, node):
        if keyword_name.lower() not in self.reserved_words:  # if there is typo in syntax, it is interpreted as keyword
            return False
        reserved_type = self.reserved_words[keyword_name.lower()]
        suffix = self.prepare_reserved_word_rule_message(keyword_name, reserved_type)
        self.report("keyword-name-is-reserved-word", keyword_name, suffix, node=node)
        return True

    @staticmethod
    def prepare_reserved_word_rule_message(name, reserved_type):
        return f". It must be in uppercase ({name.upper()}) when used as a marker with '{reserved_type}'. " \
               f"Each marker should have minimum of 2 spaces as separator." if reserved_type else ''


class SettingsNamingChecker(VisitorChecker):
    rules = {
        "0306": (
            "setting-name-not-capitalized",
            "Setting name should be capitalized or upper case",
            RuleSeverity.WARNING
        ),
        "0307": (
            "section-name-invalid",
            "Section name should should be in format '*** Capitalized ***' or '*** UPPERCASE ***'",
            RuleSeverity.WARNING
        )
    }

    def __init__(self, *args):
        self.section_name_pattern = re.compile(r'\*\*\*\s.+\s\*\*\*')
        super().__init__(*args)

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
            self.report("setting-name-not-capitalized", node=node)


class TestCaseNamingChecker(VisitorChecker):
    """ Checker for test case naming violations. """
    rules = {
        "0308": (
            "not-capitalized-test-case-title",
            "Test case title should start with capital letter",
            RuleSeverity.WARNING
        )
    }

    def visit_TestCase(self, node):  # noqa
        if not node.name[0].isupper():
            self.report("not-capitalized-test-case-title", node=node)


class VariableNamingChecker(VisitorChecker):
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
        )
    }

    def __init__(self, *args):
        self.set_variable_variants = {'settaskvariable',
                                      'settestvariable',
                                      'setsuitevariable',
                                      'setglobalvariable'}
        super().__init__(*args)

    def visit_VariableSection(self, node):  # noqa
        for child in node.body:
            if not child.data_tokens:
                continue
            token = child.data_tokens[0]
            if token.type == Token.VARIABLE and not token.value.isupper():
                self.report("section-variable-not-uppercase", lineno=token.lineno,
                            col=token.col_offset)

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:
            return
        if normalize_robot_name(node.keyword) in self.set_variable_variants:
            if len(node.data_tokens) < 2:
                return
            token = node.data_tokens[1]
            if token.type == Token.ARGUMENT and not token.value.isupper():
                self.report("non-local-variables-should-be-uppercase", node=node, col=token.col_offset + 1)
