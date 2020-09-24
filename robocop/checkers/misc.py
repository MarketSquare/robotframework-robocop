"""
Miscellaneous checkers
"""
from robot.parsing.model.statements import Return, KeywordCall
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
