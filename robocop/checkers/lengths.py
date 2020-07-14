from robot.parsing.model.statements import Documentation, Comment, KeywordCall
from robocop.checkers import VisitorChecker, RawFileChecker
from robocop.messages import MessageSeverity


def register(linter):
    linter.register_checker(LengthChecker(linter))
    linter.register_checker(LineLengthChecker(linter))


class LengthChecker(VisitorChecker):
    msgs = {
        "0501": (
            "too-long-keyword",
            "Keyword is too long (%d/%d)",
            MessageSeverity.WARNING,
            ('max_len', 'keyword_max_len', int)
        ),
        "0502": (
            "too-few-calls-in-keyword",
            "Keyword have too few keywords inside (%d/%d)",
            MessageSeverity.WARNING,
            ('min_calls', 'keyword_min_calls', int)
        ),
        "0503": (
            "too-many-calls-in-keyword",
            "Keyword have too many keywords inside (%d/%d)",
            MessageSeverity.WARNING,
            ('max_calls', 'keyword_max_calls', int)
        ),
        "0504": (
            "too-long-test-case",
            "Test case is too long (%d/%d)",
            MessageSeverity.WARNING,
            ('max_len', 'testcase_max_len', int)
        ),
        "0505": (
            "too-many-calls-in-test-case",
            "Test case have too many keywords inside (%d/%d)",
            MessageSeverity.WARNING,
            ('max_calls', 'testscase_max_calls', int)
        ),
        "0506": (
            "file-too-long",
            "File has too many lines (%d/%d)",
            MessageSeverity.WARNING,
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

    def visit_Keyword(self, node):
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

    def visit_TestCase(self, node):
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
        return sum(1 for child in node.body if isinstance(child, KeywordCall))


class LineLengthChecker(RawFileChecker):
    msgs = {
        "0507": (
            "line-too-long",
            "Line is too long (%d/%d)",
            MessageSeverity.WARNING,
            ("line_length", "max_line_length", int)
        )
    }

    def __init__(self, *args):
        self.max_line_length = 120
        super().__init__(*args)

    def visit_line(self, line, lineno):
        if len(line) > self.max_line_length:
            self.report("line-too-long", len(line), self.max_line_length, lineno=lineno)
