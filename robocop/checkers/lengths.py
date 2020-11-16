"""
Lengths checkers
"""
from robot.parsing.model.blocks import CommentSection
from robot.parsing.model.statements import KeywordCall, Comment, EmptyLine, Arguments
from robocop.checkers import VisitorChecker, RawFileChecker
from robocop.rules import RuleSeverity
from robocop.utils import normalize_robot_name


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
        ),
        "0507": (
            "too-many-arguments",
            "Keyword has too many arguments (%d/%d)",
            RuleSeverity.WARNING,
            ('max_args', 'keyword_max_args', int)
        )
    }

    def __init__(self, *args):
        self.keyword_max_len = 40
        self.testcase_max_len = 20
        self.keyword_max_calls = 8
        self.keyword_min_calls = 2
        self.testcase_max_calls = 8
        self.file_max_lines = 400
        self.keyword_max_args = 5
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
        if node.name.lstrip().startswith('#'):
            return
        for child in node.body:
            if isinstance(child, Arguments):
                args_number = len(child.values)
                if args_number > self.keyword_max_args:
                    self.report("too-many-arguments",
                                args_number,
                                self.keyword_max_args,
                                node=node)
                break
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
        "0508": (
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
        "0509": (
            "empty-section",
            "Section is empty",
            RuleSeverity.WARNING
        )
    }

    def check_if_empty(self, node):
        anything_but = EmptyLine if isinstance(node, CommentSection) else (Comment, EmptyLine)
        if all(isinstance(child, anything_but) for child in node.body):
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
        "0510": (
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

    def visit_Return(self, node):  # noqa
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


class EmptySettingsChecker(VisitorChecker):
    """ Checker for empty settings. """
    rules = {
        "0511": (
            "empty-metadata",
            "Metadata settings does not have any value set",
            RuleSeverity.WARNING
        ),
        "0512": (
            "empty-documentation",
            "Documentation is empty",
            RuleSeverity.WARNING
        ),
        "0513": (
            "empty-force-tags",
            "Force Tags are empty",
            RuleSeverity.WARNING
        ),
        "0514": (
            "empty-default-tags",
            "Default Tags are empty",
            RuleSeverity.WARNING
        ),
        "0515": (
            "empty-variables-import",
            "Import variables path is empty",
            RuleSeverity.ERROR
        ),
        "0516": (
            "empty-resource-import",
            "Import resource path is empty",
            RuleSeverity.ERROR
        ),
        "0517": (
            "empty-library-import",
            "Import library path is empty",
            RuleSeverity.ERROR
        ),
        "0518": (
            "empty-setup",
            "Setup does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0519": (
            "empty-suite-setup",
            "Suite Setup does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0520": (
            "empty-test-setup",
            "Test Setup does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0521": (
            "empty-teardown",
            "Teardown does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0522": (
            "empty-suite-teardown",
            "Suite Teardown does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0523": (
            "empty-test-teardown",
            "Test Teardown does not have any keywords",
            RuleSeverity.ERROR
        ),
        "0524": (
            "empty-timeout",
            "Timeout is empty",
            RuleSeverity.WARNING
        ),
        "0525": (
            "empty-test-timeout",
            "Test Timeout is empty",
            RuleSeverity.WARNING
        ),
        "0526": (
            "empty-arguments",
            "Arguments are empty",
            RuleSeverity.ERROR
        )
    }

    def visit_Metadata(self, node):  # noqa
        if node.name is None:
            self.report("empty-metadata", node=node, col=node.end_col_offset)

    def visit_Documentation(self, node):  # noqa
        if not node.value:
            self.report("empty-documentation", node=node, col=node.end_col_offset)

    def visit_ForceTags(self, node):  # noqa
        if not node.values:
            self.report("empty-force-tags", node=node, col=node.end_col_offset)

    def visit_DefaultTags(self, node):  # noqa
        if not node.values:
            self.report("empty-default-tags", node=node, col=node.end_col_offset)

    def visit_VariablesImport(self, node):  # noqa
        if not node.name:
            self.report("empty-variables-import", node=node, col=node.end_col_offset)

    def visit_ResourceImport(self, node):  # noqa
        if not node.name:
            self.report("empty-resource-import", node=node, col=node.end_col_offset)

    def visit_LibraryImport(self, node):  # noqa
        if not node.name:
            self.report("empty-library-import", node=node, col=node.end_col_offset)

    def visit_Setup(self, node):  # noqa
        if not node.name:
            self.report("empty-setup", node=node, col=node.end_col_offset + 1)

    def visit_SuiteSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-setup", node=node, col=node.end_col_offset)

    def visit_TestSetup(self, node):  # noqa
        if not node.name:
            self.report("empty-test-setup", node=node, col=node.end_col_offset)

    def visit_Teardown(self, node):  # noqa
        if not node.name:
            self.report("empty-teardown", node=node, col=node.end_col_offset + 1)

    def visit_SuiteTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-suite-teardown", node=node, col=node.end_col_offset)

    def visit_TestTeardown(self, node):  # noqa
        if not node.name:
            self.report("empty-test-teardown", node=node, col=node.end_col_offset)

    def visit_Timeout(self, node):  # noqa
        if not node.value:
            self.report("empty-timeout", node=node, col=node.end_col_offset + 1)

    def visit_TestTimeout(self, node):  # noqa
        if not node.value:
            self.report("empty-test-timeout", node=node, col=node.end_col_offset)

    def visit_Arguments(self, node):  # noqa
        if not node.values:
            self.report("empty-arguments", node=node, col=node.end_col_offset + 1)
