"""
Miscellaneous checkers
"""
from collections import Counter
from robot.parsing.model.statements import Return, KeywordCall, EmptyLine
from robot.parsing.model.blocks import ForLoop
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
        self.check_indents(node)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        self.check_indents(node, node.header.tokens[1].col_offset)

    def check_indents(self, node, req_indent=0):
        indents = []
        tab_type = None
        for child in node.body:
            if isinstance(child, EmptyLine):
                continue
            if isinstance(child, ForLoop):
                indent_len = len(child.header.tokens[0].value.replace('\t', 4*' '))
                if indent_len < req_indent:
                    self.report("bad-indent", node=child)
                indents.append((indent_len, child))
            else:
                indent_len = len(child.tokens[0].value.replace('\t', 4*' '))
                if indent_len < req_indent:
                    self.report("bad-indent", node=child)
                indents.append((indent_len, child))
        if len(indents) < 2:
            return
        counter = Counter(indent[0] for indent in indents)
        if len(counter) == 1:  # everything have the same indent
            return
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report("ineven-indent", 'over' if indent[0] > common_indent else 'under', node=indent[1])