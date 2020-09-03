"""
Naming checkers
"""
from pathlib import Path
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity


def register(linter):
    linter.register_checker(InvalidCharactersInNameChecker(linter))
    linter.register_checker(KeywordNamesChecker(linter))


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


class KeywordNamesChecker(VisitorChecker):
    """ Checker for naming keyword violation. """
    rules = {
        "0302": (
            "not-capitalized-keyword-name",
            "Keyword name should be capitalized",
            RuleSeverity.WARNING
        ),
        "0303": (
            "reserved-word-keyword-name",
            "'%s' is a reserved keyword%s",
            RuleSeverity.ERROR
        )
    }
    reserved_words = {
                         'for': 'for loop',
                         'end': 'for loop',
                         'else if': 'Run Keyword If',
                         'else': 'Run Keyword If',
                         'while': '',
                         'continue': ''
    }

    def visit_SuiteSetup(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_TestSetup(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_Setup(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_SuiteTeardown(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_TestTeardown(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_Teardown(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.name, node)

    def visit_TestCase(self, node):  # noqa
        self.generic_visit(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name.lstrip().startswith('#'):
            self.check_if_keyword_is_capitalized(node.name, node)
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        self.check_if_keyword_is_capitalized(node.keyword, node)

    def check_if_keyword_is_capitalized(self, keyword_name, node):  # noqa
        if keyword_name == r'/':  # old for loop, / are interpreted as keywords
            return
        if self.check_if_keyword_is_reserved(keyword_name, node):
            return
        words = keyword_name.replace('_', ' ').split(' ')
        if any(not word.istitle() for word in words):
            self.report("not-capitalized-keyword-name", node=node)

    def check_if_keyword_is_reserved(self, keyword_name, node):
        if keyword_name.lower() not in self.reserved_words:  # if there is typo in syntax, it is interpreted as keyword
            return False
        reserved_type = self.reserved_words[keyword_name.lower()]
        suffix = f". It must be in uppercase ({keyword_name.upper()}) when used as a marker with '{reserved_type}'." \
            if reserved_type else ''
        self.report("reserved-word-keyword-name", keyword_name, suffix, node=node)
        return True