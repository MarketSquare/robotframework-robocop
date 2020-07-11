from robot.parsing.model.statements import Documentation, Comment
from robocop.checkers import BaseChecker
from robocop.messages import MessageSeverity


MSGS = {
    "0301": (
        "invalid-char-in-name",
        "Invalid character %s in %s name",
        MessageSeverity.WARNING
    )
}


def register(linter):
    linter.register_checker(InvalidCharactersInNameChecker(linter))


class InvalidCharactersInNameChecker(BaseChecker):
    msgs = MSGS

    def __init__(self, *args):
        self.invalid_chars = ('.', '?')
        configurable = {'invalid_chars'}
        self.node_names_map = {
            'KEYWORD_NAME': 'keyword',
            'TESTCASE_NAME': 'test case'
        }
        super().__init__(*args, configurable=configurable)

    def configure(self, **kwargs):
        for kwarg, value in kwargs.items():
            if kwarg not in self.configurable:
                raise ValueError(f"{kwarg} parameter is not configurable")
            self.__dict__[kwarg] = set(value)
    
    def check_if_char_in_name(self, node, name_of_node):
        # if self.is_disabled(node, "invalid-char-in-name"):
        #     return
        for index, char in enumerate(node.name):
            if char in self.invalid_chars:
                self.report("invalid-char-in-name", char, self.node_names_map[name_of_node],
                            node=node,
                            col=node.col_offset + index + 1)

    def visit_TestCaseName(self, node):
        self.check_if_char_in_name(node, 'TESTCASE_NAME')
        
    def visit_KeywordName(self, node):
        self.check_if_char_in_name(node, 'KEYWORD_NAME')