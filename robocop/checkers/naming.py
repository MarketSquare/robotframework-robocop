"""
Naming checkers
"""
from robocop.checkers import VisitorChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(InvalidCharactersInNameChecker(linter))


class InvalidCharactersInNameChecker(VisitorChecker):
    """ Checker for invalid characters in test case or keyword name. """
    msgs = {
        "0301": (
            "invalid-char-in-name",
            "Invalid character %s in %s name",
            MessageSeverity.WARNING,
            ('invalid_chars', 'invalid_chars', set)
        )
    }

    def __init__(self, *args):
        self.invalid_chars = ('.', '?')
        self.node_names_map = {
            'KEYWORD_NAME': 'keyword',
            'TESTCASE_NAME': 'test case'
        }
        super().__init__(*args)
    
    def check_if_char_in_name(self, node, name_of_node):
        for index, char in enumerate(node.name):
            if char in self.invalid_chars:
                self.report("invalid-char-in-name", char, self.node_names_map[name_of_node],
                            node=node,
                            col=node.col_offset + index + 1)

    def visit_TestCaseName(self, node):
        self.check_if_char_in_name(node, 'TESTCASE_NAME')
        
    def visit_KeywordName(self, node):
        self.check_if_char_in_name(node, 'KEYWORD_NAME')