"""
Errors checkers
"""
import re

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import IS_RF4


class ParsingErrorChecker(VisitorChecker):
    """ Checker that parse Robot Framework DataErrors. """
    rules = {
        "0401": (
            "parsing-error",
            "Robot Framework syntax error: %s",
            RuleSeverity.ERROR
        ),
        "0405": (
            "invalid-continuation-mark",
            "Invalid continuation mark. It should be: '...'",
            RuleSeverity.ERROR
        ),
        "0406": (
            # there is not-enough-whitespace-after-newline-marker for keyword calls already
            "not-enough-whitespace-after-newline-marker-error",
            "Provide at least two spaces after '...' marker",
            RuleSeverity.ERROR
        )
    }
    def visit_If(self, node):  # noqa
        self.parse_errors(node)
        self.generic_visit(node)

    def visit_For(self, node):  # noqa
        self.parse_errors(node)
        self.generic_visit(node)

    def visit_Statement(self, node):  # noqa
        self.parse_errors(node)

    def parse_errors(self, node):  # noqa
        if node is None:
            return
        if IS_RF4:
            for error in node.errors:
                self.handle_error(node, error)
        else:
            self.handle_error(node, node.error)

    def handle_error(self, node, error):  # noqa
        if not error:
            return
        if re.search(r"Non-existing setting '\s*\.\.", error):
            self.handle_invalid_continuation_mark(node, node.data_tokens[0].value)
            return
        if re.search(r"Invalid variable name '\s*\.\.", error):
            name = node.name if hasattr(node, 'name') else error.replace("Invalid variable name '", "")
            self.handle_invalid_continuation_mark(node, name)
            return
        error = error.replace('\n   ', '')
        self.report("parsing-error", error, node=node)

    def handle_invalid_continuation_mark(self, node, name):
        stripped = name.lstrip()
        if stripped.startswith('..'):
            if len(name) == 2 or not stripped[2].strip():
                self.report("invalid-continuation-mark", node=node, col=name.find('.') + 1)
            elif len(stripped) >= 4:
                if stripped[:4] == '....':
                    self.report("invalid-continuation-mark", node=node, col=name.find('.') + 1)
                else:  # '... ' or '...value' or '...\t'
                    self.report("not-enough-whitespace-after-newline-marker-error", node=node, col=name.find('.') + 1)


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
