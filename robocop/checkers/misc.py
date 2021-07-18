"""
Miscellaneous checkers
"""
from robot.api import Token
from robot.parsing.model.statements import Return, KeywordCall
try:
    from robot.api.parsing import Variable
except ImportError:
    from robot.parsing.model.statements import Variable
from robot.libraries import STDLIBS

from robocop.checkers import VisitorChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name, IS_RF4, AssignmentTypeDetector, parse_assignment_sign_type


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


class NestedForLoopsChecker(VisitorChecker):
    """ Checker for not supported nested FOR loops.

    Deprecated in RF 4.0
    """
    rules = {
        "0907": (
            "nested-for-loop",
            "Nested for loops are not supported. You can use keyword with for loop instead",
            RuleSeverity.ERROR
        )
    }

    def __init__(self):
        super().__init__()
        if IS_RF4:
            self.disabled = True

    def visit_ForLoop(self, node):  # noqa
        # For RF 4.0 node is "For" but we purposely don't visit it because nested for loop is allowed in 4.0
        for child in node.body:
            if child.type == 'FOR':
                self.report("nested-for-loop", node=child)


class IfBlockCanBeUsed(VisitorChecker):
    """ Checker for potential IF block usage in Robot Framework 4.0

    Run Keyword variants (Run Keyword If, Run Keyword Unless) can be replaced with IF in RF 4.0
    """
    rules = {
        "0908": (
            "if-can-be-used",
            "'%s' can be replaced with IF block since Robot Framework 4.0",
            RuleSeverity.INFO
        )
    }

    def __init__(self):
        self.run_keyword_variants = {'runkeywordif', 'runkeywordunless'}
        super().__init__()
        if not IS_RF4:
            self.disabled = True

    def visit_KeywordCall(self, node):  # noqa
        if not node.keyword:
            return
        if normalize_robot_name(node.keyword) in self.run_keyword_variants:
            col = 0
            for token in node.data_tokens:
                if token.type == Token.KEYWORD:
                    col = token.col_offset + 1
                    break
            self.report("if-can-be-used", node.keyword, node=node, col=col)


class ConsistentAssignmentSignChecker(VisitorChecker):
    """ Checker for inconsistent assignment signs.

    By default this checker will try to autodetect most common assignment sign (separately for *** Variables *** section
    and (*** Test Cases ***, *** Keywords ***) sections and report any not consistent type of sign in particular file.

    To force one type of sign type (to emulate now deprecated ``0906 (redundant-equal-sign)`` rule) you can configure
    two rules::

        --configure inconsistent-assignment:assignment_sign_type:{sign_type}
        --configure inconsistent-assignment-in-variables:assignment_sign_type:{sign_type}

    ``${sign_type}` can be one of: ``autodetect`` (default), ``none`` (''), ``equal_sign`` ('='),
    ``space_and_equal_sign`` (' =').

    """
    rules = {
        "0909": (
            "inconsistent-assignment",
            "The assignment sign is not consistent through the file. Expected '%s' but got '%s' instead",
            RuleSeverity.WARNING,
            (
                'assignment_sign_type',
                'keyword_assignment_sign_type',
                parse_assignment_sign_type,
                "possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') "
                "or space_and_equal_sign (' =')"
             )
        ),
        "0910": (
            "inconsistent-assignment-in-variables",
            "The assignment sign is not consistent inside the variables section. Expected '%s' but got '%s' instead",
            RuleSeverity.WARNING,
            (
                'assignment_sign_type',
                'variables_assignment_sign_type',
                parse_assignment_sign_type,
                "possible values: 'autodetect' (default), 'none' (''), 'equal_sign' ('=') "
                "or space_and_equal_sign (' =')"
            )
        )
    }

    def __init__(self):
        self.keyword_assignment_sign_type = 'autodetect'
        self.variables_assignment_sign_type = 'autodetect'
        self.keyword_expected_sign_type = None
        self.variables_expected_sign_type = None
        super().__init__()

    def visit_File(self, node):  # noqa
        self.keyword_expected_sign_type = self.keyword_assignment_sign_type
        self.variables_expected_sign_type = self.variables_assignment_sign_type
        if 'autodetect' in [self.keyword_assignment_sign_type, self.variables_assignment_sign_type]:
            auto_detector = self.auto_detect_assignment_sign(node)
            if self.keyword_assignment_sign_type == 'autodetect':
                self.keyword_expected_sign_type = auto_detector.keyword_most_common
            if self.variables_assignment_sign_type == 'autodetect':
                self.variables_expected_sign_type = auto_detector.variables_most_common
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa
        if self.keyword_expected_sign_type is None or not node.keyword:
            return
        if node.assign:  # if keyword returns any value
            assign_tokens = node.get_tokens(Token.ASSIGN)
            self.check_assign_type(assign_tokens[-1], self.keyword_expected_sign_type, "inconsistent-assignment")
        return node

    def visit_VariableSection(self, node):  # noqa
        if self.variables_expected_sign_type is None:
            return
        for child in node.body:
            if not isinstance(child, Variable) or getattr(child, 'errors', None) or getattr(child, 'error', None):
                continue
            var_token = child.get_token(Token.VARIABLE)
            self.check_assign_type(
                var_token,
                self.variables_expected_sign_type,
                "inconsistent-assignment-in-variables"
            )
        return node

    def check_assign_type(self, token, expected, issue_name):
        sign = AssignmentTypeDetector.get_assignment_sign(token.value)
        if sign != expected:
            self.report(issue_name, expected, sign, lineno=token.lineno, col=token.end_col_offset + 1)

    @staticmethod
    def auto_detect_assignment_sign(node):
        auto_detector = AssignmentTypeDetector()
        auto_detector.visit(node)
        return auto_detector


class SettingsOrderChecker(VisitorChecker):
    """ Checker for settings order.

    BuiltIn libraries imports should always be placed before other libraries imports.
    """
    rules = {
        "0911": (
            "wrong-import-order",
            "BuiltIn library import '%s' should be placed before '%s'",
            RuleSeverity.WARNING
        )
    }

    def __init__(self):
        self.libraries = []
        super().__init__()

    def visit_File(self, node):  # noqa
        self.libraries = []
        self.generic_visit(node)
        first_non_builtin = None
        for library in self.libraries:
            if first_non_builtin is None:
                if library.name not in STDLIBS:
                    first_non_builtin = library.name
            else:
                if library.name in STDLIBS:
                    self.report("wrong-import-order", library.name, first_non_builtin, node=library)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            return
        self.libraries.append(node)
