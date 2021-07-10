"""
Errors checkers
"""
import re

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import IS_RF4


class ParsingErrorChecker(VisitorChecker):
    """ Checker that returns Robot Framework DataErrors as lint errors. """
    rules = {
        "0401": (
            "parsing-error",
            "Robot Framework syntax error: %s",
            RuleSeverity.ERROR
        )
    }
    def visit_If(self, node):  # noqa
        self.handle_errors(node)
        self.handle_errors(node.header)
        self.generic_visit(node)

    def visit_For(self, node):  # noqa
        self.handle_errors(node)
        self.handle_errors(node.header)
        self.generic_visit(node)

    def visit_Error(self, node):  # noqa
        self.handle_errors(node)

    def handle_errors(self, node):  # noqa
        if node is None:
            return
        if IS_RF4:
            for error in node.errors:
                self.report("parsing-error", error, node=node)
        else:
            self.report("parsing-error", node.error, node=node)


class TwoSpacesAfterSettingsChecker(VisitorChecker):
    """ Checker for not enough whitespaces after [Setting] header. """
    rules = {
        "0402": (
            "missing-whitespace-after-setting",
            "There should be at least two spaces after the %s setting",
            RuleSeverity.ERROR
        )
    }

    def __init__(self):
        self.headers = {'arguments', 'documentation', 'setup', 'timeout', 'teardown', 'template', 'tags'}
        self.setting_pattern = re.compile(r'\[\s?(\w+)\s?\]')
        super().__init__()

    def visit_KeywordCall(self, node):  # noqa
        """ Invalid settings like '[Arguments] ${var}' will be parsed as keyword call """
        if not node.keyword:
            return

        match = self.setting_pattern.match(node.keyword)
        if not match:
            return
        if match.group(1).lower() in self.headers:
            self.report(
                "missing-whitespace-after-setting",
                match.group(0),
                node=node,
                col=node.data_tokens[0].col_offset + 1
            )


class MissingKeywordName(VisitorChecker):
    """ Checker for missing keyword name. """
    rules = {
        "0403": (
            "missing-keyword-name",
            "Missing keyword name when calling some values",
            RuleSeverity.ERROR
        )
    }

    def visit_KeywordCall(self, node):  # noqa
        if node.keyword is None:
            self.report(
                "missing-keyword-name",
                node=node,
                lineno=node.lineno,
                col=node.data_tokens[0].col_offset + 1
            )
