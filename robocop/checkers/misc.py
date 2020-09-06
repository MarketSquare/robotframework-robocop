"""
Miscellaneous checkers
"""
from collections import Counter
from robot.parsing.model.statements import Return, KeywordCall, EmptyLine
from robot.parsing.model.blocks import ForLoop
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


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

    def __init__(self, *args):
        self.headers = {'arguments', 'documentation', 'setup', 'timeout', 'teardown', 'template', 'tags'}
        super().__init__(*args)

    def visit_TestCase(self, node):  # noqa
        self.check_indents(node)

    def visit_Keyword(self, node):  # noqa
        if not node.name.lstrip().startswith('#'):
            self.check_indents(node)
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        column_index = 2 if node.end is None else 0
        self.check_indents(node, node.header.tokens[1].col_offset + 1, column_index)

    @staticmethod
    def get_indent(node, column_index):
        if isinstance(node, ForLoop):
            separator = node.header.tokens[column_index]
        else:
            separator = node.tokens[column_index]
        if separator.type == 'SEPARATOR':
            return len(separator.value.expandtabs(4))
        if separator.type in ('COMMENT', 'EOL'):
            return None
        return 0

    def check_indents(self, node, req_indent=0, column_index=0):
        indents = []
        header_indents = []
        for child in node.body:
            if hasattr(child, 'type') and child.type == 'TEMPLATE':
                templated = True
                break
        else:
            templated = False
        for child in node.body:
            if isinstance(child, EmptyLine):
                continue
            indent_len = self.get_indent(child, column_index)
            if indent_len is None:
                continue
            if hasattr(child, 'type') and child.type.strip().lower() in self.headers:
                if templated:
                    header_indents.append((indent_len, child))
                else:
                    indents.append((indent_len, child))
            else:
                indents.append((indent_len, child))
                if not column_index and (indent_len < req_indent):
                    self.report("bad-indent", node=child)
        self.validate_indent_lists(indents)
        if templated:
            self.validate_indent_lists(header_indents)

    def validate_indent_lists(self, indents):
        if len(indents) < 2:
            return
        counter = Counter(indent[0] for indent in indents)
        if len(counter) == 1:  # everything have the same indent
            return
        common_indent = counter.most_common(1)[0][0]
        for indent in indents:
            if indent[0] != common_indent:
                self.report("ineven-indent", 'over' if indent[0] > common_indent else 'under',
                            node=indent[1],
                            col=indent[0] + 1)
