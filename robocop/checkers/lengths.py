"""
Lengths checkers
"""
from robot.parsing.model.statements import KeywordCall, Comment, EmptyLine, Return
from robocop.checkers import VisitorChecker, RawFileChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


def register(linter):
    linter.register_checker(LengthChecker(linter))
    linter.register_checker(LineLengthChecker(linter))
    linter.register_checker(EmptySectionChecker(linter))
    linter.register_checker(NumberOfReturnedArgsChecker(linter))


class LengthChecker(VisitorChecker):
    """ Checker for max and min length of keyword or test case. It analyses number of lines and also number of
        keyword calls (as you can have just few keywords but very long ones or vice versa).
    """
    rules = {
        "0501": (
            "too-long-keyword",
            "Keyword is too long (%d/%d)",
            RuleSeverity.WARNING,
            ('max_len', 'keyword_max_len', int)
        ),
        "0502": (
            "too-few-calls-in-keyword",
            "Keyword have too few keywords inside (%d/%d)",
            RuleSeverity.WARNING,
            ('min_calls', 'keyword_min_calls', int)
        ),
        "0503": (
            "too-many-calls-in-keyword",
            "Keyword have too many keywords inside (%d/%d)",
            RuleSeverity.WARNING,
            ('max_calls', 'keyword_max_calls', int)
        ),
        "0504": (
            "too-long-test-case",
            "Test case is too long (%d/%d)",
            RuleSeverity.WARNING,
            ('max_len', 'testcase_max_len', int)
        ),
        "0505": (
            "too-many-calls-in-test-case",
            "Test case have too many keywords inside (%d/%d)",
            RuleSeverity.WARNING,
            ('max_calls', 'testcase_max_calls', int)
        ),
        "0506": (
            "file-too-long",
            "File has too many lines (%d/%d)",
            RuleSeverity.WARNING,
            ('max_lines', 'file_max_lines', int)
        )
    }

    def __init__(self, *args):
        self.keyword_max_len = 40
        self.testcase_max_len = 20
        self.keyword_max_calls = 8
        self.keyword_min_calls = 2
        self.testcase_max_calls = 8
        self.file_max_lines = 400
        super().__init__(*args)

    def visit_File(self, node):
        if node.end_lineno > self.file_max_lines:
            self.report("file-too-long",
                        node.end_lineno,
                        self.file_max_lines,
                        node=node,
                        lineno=node.end_lineno)
        super().visit_File(node)

    def visit_Keyword(self, node):  # noqa
        length = LengthChecker.check_node_length(node)
        if length > self.keyword_max_len:
            self.report("too-long-keyword",
                        length,
                        self.keyword_max_len,
                        node=node,
                        lineno=node.end_lineno)
            return
        key_calls = LengthChecker.count_keyword_calls(node)
        if key_calls < self.keyword_min_calls:
            self.report("too-few-calls-in-keyword",
                        key_calls,
                        self.keyword_min_calls,
                        node=node)
            return
        if key_calls > self.keyword_max_calls:
            self.report("too-many-calls-in-keyword",
                        key_calls,
                        self.keyword_max_calls,
                        node=node)
            return

    def visit_TestCase(self, node):  # noqa
        length = LengthChecker.check_node_length(node)
        if length > self.testcase_max_len:
            self.report("too-long-test-case",
                        length,
                        self.testcase_max_len,
                        node=node)
        key_calls = LengthChecker.count_keyword_calls(node)
        if key_calls > self.testcase_max_calls:
            self.report("too-many-calls-in-test-case",
                        key_calls,
                        self.testcase_max_calls,
                        node=node)
            return

    @staticmethod
    def check_node_length(node):
        return node.end_lineno - node.lineno

    @staticmethod
    def count_keyword_calls(node):
        if isinstance(node, KeywordCall):
            return 1
        if not hasattr(node, 'body'):
            return 0
        return sum(LengthChecker.count_keyword_calls(child) for child in node.body)


class LineLengthChecker(RawFileChecker):
    """ Checker for max length of line. """
    rules = {
        "0507": (
            "line-too-long",
            "Line is too long (%d/%d)",
            RuleSeverity.WARNING,
            ("line_length", "max_line_length", int)
        )
    }

    def __init__(self, *args):
        self.max_line_length = 120
        super().__init__(*args)

    def check_line(self, line, lineno):
        if len(line) > self.max_line_length:
            self.report("line-too-long", len(line), self.max_line_length, lineno=lineno)


class EmptySectionChecker(VisitorChecker):
    """ Checker for empty section. """
    rules = {
        "0508": (
            "empty-section",
            "Section is empty",
            RuleSeverity.WARNING
        )
    }

    def check_if_empty(self, node):
        for child in node.body:
            if isinstance(child, Comment):
                if 'robocop:' in child.tokens[0].value and len(node.body) == 1:
                    break
            elif not isinstance(child, EmptyLine):
                break
        else:
            self.report("empty-section", node=node)

    def visit_SettingSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_VariableSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_TestCaseSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_KeywordSection(self, node):  # noqa
        self.check_if_empty(node)

    def visit_CommentSection(self, node):  # noqa
        self.check_if_empty(node)


class NumberOfReturnedArgsChecker(VisitorChecker):
    """ Checker for number of returned values from keyword. """
    rules = {
        "0509": (
            "number-of-returned-values",
            "Too many return values (%d/%d)",
            RuleSeverity.WARNING,
            ("max_returns", "max_returns", int)
        )
    }

    def __init__(self, *args):
        self.max_returns = 4
        super().__init__(*args)

    def visit_Keyword(self, node):  # noqa
        self.generic_visit(node)

    def visit_ForLoop(self, node):  # noqa
        self.generic_visit(node)

    def visit_Return(self, node):
        self.check_node_returns(len(node.values), node)

    def visit_KeywordCall(self, node):  # noqa
        normalized_name = normalize_robot_name(node.keyword)
        if normalized_name == 'returnfromkeyword':
            self.check_node_returns(len(node.args), node)
        elif normalized_name == 'returnfromkeywordif':
            self.check_node_returns(len(node.args) - 1, node)

    def check_node_returns(self, return_count, node):
        if return_count > self.max_returns:
            self.report("number-of-returned-values", return_count, self.max_returns, node=node)