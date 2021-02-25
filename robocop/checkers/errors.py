"""
Errors checkers
"""
import re

from robot.version import VERSION as ROBOT_VERSION

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

    def visit_Error(self, node):  # noqa
        if IS_RF4:
            for error in node.errors:
                self.report("parsing-error", error, node=node)
        else:
            self.report("parsing-error", node.error, node=node)


class TwoSpacesAfterSettingsChecker(VisitorChecker):
    """ Checker for not enough whitespace after [Setting] header. """
    rules = {
        "0402": (
            "missing-whitespace-after-setting",
            "There should be at least two spaces after the %s setting",
            RuleSeverity.ERROR
        )
    }

    def __init__(self, *args):
        self.headers = {'arguments', 'documentation', 'setup', 'timeout', 'teardown', 'template', 'tags'}
        self.setting_pattern = re.compile(r'\[\s?(\w+)\s?\]')
        super().__init__(*args)

    def visit_KeywordCall(self, node):  # noqa
        """ Invalid settings like '[Arguments] ${var}' will be parsed as keyword call """
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
