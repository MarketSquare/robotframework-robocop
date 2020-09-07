"""
Miscellaneous checkers
"""
from collections import Counter
from robot.parsing.model.statements import Return, KeywordCall, EmptyLine
from robot.parsing.model.blocks import ForLoop
from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


class ReturnChecker(VisitorChecker):
    """ Checker for [Return] and Return From Keyword violations. """
    rules = {
        "0901": (
            "keyword-after-return",
            "[Return] is not defined at the end of keyword. "
            "Note that [Return] does not return from keyword but only set returned variables",
            RuleSeverity.WARNING
        ),
        "0902": (
            "keyword-after-return-from",
            "Keyword call after 'Return From Keyword' keyword",
            RuleSeverity.ERROR
        ),
        "0903": (
            "empty-return",
            "[Return] is empty",
            RuleSeverity.WARNING
        )
    }

    def visit_Keyword(self, node):  # noqa
        return_setting_node = None
        keyword_after_return = False
        return_from = False
        for child in node.body:
            if isinstance(child, Return):
                return_setting_node = child
                if not child.values:
                    self.report("empty-return", node=child, col=child.end_col_offset)
            elif isinstance(child, KeywordCall):
                if return_setting_node is not None:
                    keyword_after_return = True
                if return_from:
                    self.report("keyword-after-return-from", node=child)
                if normalize_robot_name(child.keyword) == 'returnfromkeyword':
                    return_from = True
        if keyword_after_return:
            self.report(
                "keyword-after-return",
                node=return_setting_node,
                col=return_setting_node.end_col_offset
            )


class InevenIndentChecker(VisitorChecker):
    """ Checker for ineven indendation. """
    rules = {
        "0904": (
            "ineven-indent",
            "Line is %s-indented",
            RuleSeverity.WARNING
        ),
        "0905": (
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


class EqualSignChecker(VisitorChecker):
    """ Checker for redundant equal signs when assigning return values. """
    rules = {
        "0906": (
            "redundant-equal-sign",
            "Redundant equal sign in return value assignment",
            RuleSeverity.WARNING
        )
    }

    def visit_KeywordCall(self, node):  # noqa
        if node.assign:  # if keyword returns any value
            if node.assign[-1][-1] == '=':  # last character of last assigned variable
                equal_position = [x for x in node.data_tokens if x.type == 'ASSIGN'][-1].end_col_offset
                self.report("redundant-equal-sign", lineno=node.lineno, col=equal_position)


class NestedForLoopsChecker(VisitorChecker):
    """ Checker for not supported nested FOR loops. """
    rules = {
        "0907": (
            "nested-for-loop",
            "Nested for loops are not supported. You can use keyword with for loop instead",
            RuleSeverity.ERROR
        )
    }

    def visit_ForLoop(self, node):  # noqa
        for child in node.body:
            if child.type == 'FOR':
                self.report("nested-for-loop", node=child)
