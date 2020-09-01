"""
Miscellaneous checkers
"""
from collections import Counter
from robot.parsing.model.statements import Return, KeywordCall, EmptyLine, Documentation, Timeout, Arguments, Setup, Teardown, Template
from robot.parsing.model.blocks import ForLoop, LastStatementFinder
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


def register(linter):
    linter.register_checker(EarlyReturnChecker(linter))
    linter.register_checker(InevenIndentChecker(linter))


class EarlyReturnChecker(VisitorChecker):
    """ Checker for keyword calls after [Return] statement. """
    rules = {
        "0901": (
            "keyword-after-return",
            "Keyword call after %s statement",
            RuleSeverity.ERROR
        )
    }

    def visit_Keyword(self, node):  # noqa
        returned = ''
        for child in node.body:
            if isinstance(child, Return):
                returned = '[Return]'
            elif isinstance(child, KeywordCall):
                if returned:
                    self.report("keyword-after-return", returned, node=child)
                if normalize_robot_name(child.keyword) == 'returnfromkeyword':
                    returned = 'Return From Keyword'


class InevenIndentChecker(VisitorChecker):
    """ Checker for ineven indendation. """
    rules = {
        "0902": (
            "ineven-indent",
            "Line is %s-indented",
            RuleSeverity.WARNING
        ),
        "0903": (
            "bad-indent",
            "Indent expected",
            RuleSeverity.ERROR
        )
    }

    def visit_TestCase(self, node):  # noqa
        self.check_indents(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name.lstrip().startswith('#'):
            self.check_indents(node)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        self.check_indents(node, node.header.tokens[1].col_offset + 1)

    def check_indents(self, node, req_indent=0):
        indents = []
        statement_indents = []
        tab_type = None
        for child in node.body:
            if isinstance(child, EmptyLine):
                continue
            if isinstance(child, ForLoop):
                if child.header.tokens[0].type == 'SEPARATOR':
                    indent_len = len(child.header.tokens[0].value.replace('\t', 4*' '))
                elif child.header.tokens[0].type == 'COMMENT':
                    continue
                else:
                    indent_len = 0
                if indent_len < req_indent:
                    self.report("bad-indent", node=child)
                indents.append((indent_len, child))
            elif isinstance(child, (Arguments, Documentation, Setup, Timeout, Teardown, Template)):
                if child.tokens[0].type == 'SEPARATOR':
                    indent_len = len(child.tokens[0].value.replace('\t', 4*' '))
                elif child.tokens[0].type == 'COMMENT':
                    continue
                else:
                    indent_len = 0
                statement_indents.append((indent_len, child))
            else:
                if child.tokens[0].type == 'SEPARATOR':
                    indent_len = len(child.tokens[0].value.replace('\t', 4*' '))
                elif child.tokens[0].type == 'COMMENT':
                    continue
                else:
                    indent_len = 0
                if indent_len < req_indent:
                    self.report("bad-indent", node=child)
                indents.append((indent_len, child))
        self.validate_indent_lists(indents)
        self.validate_indent_lists(statement_indents)

    def validate_indent_lists(self, indents):
        if len(indents) < 2:
            return
        counter = Counter(indent[0] for indent in indents)
        if len(counter) == 1:  # everything have the same indent
            return
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report("ineven-indent", 'over' if indent[0] > common_indent else 'under', node=indent[1])
