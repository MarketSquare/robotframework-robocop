"""
Errors checkers
"""
import re

from robot.api import Token

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import IS_RF4, find_robot_vars


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
            "Invalid continuation mark. It should be '...'",
            RuleSeverity.ERROR
        ),
        "0406": (
            # there is not-enough-whitespace-after-newline-marker for keyword calls already
            "not-enough-whitespace-after-newline-marker-error",
            "Provide at least two spaces after '...' marker",
            RuleSeverity.ERROR
        ),
        "0407": (
            "invalid-argument",
            "%s",
            RuleSeverity.ERROR
        ),
        "0408": (
            "non-existing-setting",
            "%s",
            RuleSeverity.ERROR
        ),
        "0409": (
            "setting-not-supported",
            "Setting '[%s]' is not supported in %s. Allowed are: %s",
            RuleSeverity.ERROR
        ),
        "0410": (
            "not-enough-whitespace-after-variable",
            "Provide at least two spaces after variable",
            RuleSeverity.ERROR
        )
    }
    keyword_only_settings = {'Arguments', 'Return'}
    keyword_settings = ['[Documentation]', '[Tags]', '[Arguments]', '[Return]', '[Teardown]', '[Timeout]']
    test_case_only_settings = {'Setup', 'Template'}
    test_case_settings = ['[Documentation]', '[Tags]', '[Setup]', '[Teardown]', '[Template]', '[Timeout]']

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
        if 'Invalid argument syntax' in error:
            self.handle_invalid_syntax(node, error)
        elif 'Non-existing setting' in error:
            self.handle_invalid_setting(node, error)
        elif 'Invalid variable name' in error:
            self.handle_invalid_variable(node, error)
        else:
            error = error.replace('\n   ', '')
            self.report("parsing-error", error, node=node)

    def handle_invalid_syntax(self, node, error):
        # robot doesn't report on exact token, so we need to find it
        match = re.search("'(.+)'", error)
        if not match:
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            value, *_ = arg.value.split('=', maxsplit=1)
            if value == match.group(1):
                self.report("invalid-argument", error[:-1], node=arg, col=arg.col_offset + 1)
                return
        self.report("parsing-error", error, node=node)

    def handle_invalid_setting(self, node, error):
        setting_error = re.search("Non-existing setting '(.*)'.", error)
        if not setting_error:
            return
        setting_error = setting_error.group(1)
        if not setting_error:  # TODO should be left aligned
            return
        if setting_error.lstrip().startswith('..'):
            self.handle_invalid_continuation_mark(node, node.data_tokens[0].value)
        elif setting_error in self.keyword_only_settings:
            self.report("setting-not-supported", setting_error, 'Test Case', ', '.join(self.test_case_settings),
                        node=node)
        elif setting_error in self.test_case_only_settings:
            self.report("setting-not-supported", setting_error, 'Keyword', ', '.join(self.keyword_settings), node=node)
        else:
            error = error.replace('\n   ', '').replace('Robot Framework syntax error: ', '')
            if error.endswith('.'):
                error = error[:-1]
            self.report("non-existing-setting", error, node=node)

    def handle_invalid_variable(self, node, error):
        var_error = re.search("Invalid variable name '(.*)'.", error)
        if not var_error or not var_error.group(1):  # empty variable name due to invalid parsing
            return
        elif var_error.group(1).lstrip().startswith('..'):
            self.handle_invalid_continuation_mark(node, var_error.group(1))
        elif not var_error.group(1)[0].strip():  # not left aligned variable
            return
        else:
            variable_token = node.get_token(Token.VARIABLE)
            variables = find_robot_vars(variable_token.value) if variable_token else None
            if variables and variables[0][0] == 0:
                self.report("not-enough-whitespace-after-variable", node=variable_token,
                            col=variable_token.col_offset + 1)
            else:
                error = error.replace('\n   ', '')
                self.report("parsing-error", error, node=node)

    def handle_invalid_continuation_mark(self, node, name):
        stripped = name.lstrip()
        if len(stripped) == 2 or not stripped[2].strip():
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
