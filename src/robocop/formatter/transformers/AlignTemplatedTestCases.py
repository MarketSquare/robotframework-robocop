from robot.api.parsing import (
    Comment,
    ElseHeader,
    ElseIfHeader,
    EmptyLine,
    End,
    ForHeader,
    IfHeader,
    ModelVisitor,
    Template,
    Token,
)
from robotidy.disablers import skip_if_disabled, skip_section_if_disabled
from robotidy.transformers import Transformer
from robotidy.utils import misc


class AlignTemplatedTestCases(Transformer):
    """
    Align templated Test Cases to columns.

    Following code:

    ```robotframework
    *** Test Cases ***    baz    qux
    # some comment
    test1    hi    hello
    test2 long test name    asdfasdf    asdsdfgsdfg
    ```

    will be transformed to:

    ```robotframework
    *** Test Cases ***      baz         qux
    # some comment
    test1                   hi          hello
    test2 long test name    asdfasdf    asdsdfgsdfg
                            bar1        bar2
    ```

    If you don't want to align test case section that does not contain header names (in above example baz and quz are
    header names) then configure `only_with_headers` parameter:

    ```
    robotidy -c AlignSettingsSection:only_with_headers:True <src>
    ```

    For non-templated test cases use ``AlignTestCasesSection`` transformer.
    """

    ENABLED = False

    def __init__(self, only_with_headers: bool = False, min_width: int = None):
        super().__init__()
        self.only_with_headers = only_with_headers
        self.min_width = min_width
        self.widths = None
        self.test_name_len = 0
        self.test_without_eol = False
        self.indent = 0

    def visit_File(self, node):  # noqa
        if not misc.is_suite_templated(node):
            return node
        self.test_without_eol = False
        return self.generic_visit(node)

    def visit_If(self, node):  # noqa
        self.indent += 1
        self.generic_visit(node)
        self.indent -= 1
        return node

    visit_Else = visit_ElseIf = visit_For = visit_If

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node):  # noqa
        if len(node.header.data_tokens) == 1 and self.only_with_headers:
            return node
        counter = ColumnWidthCounter(self.disablers)
        counter.visit(node)
        self.widths = counter.widths
        return self.generic_visit(node)

    def visit_TestCase(self, node):  # noqa
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return node
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, statement):  # noqa
        if statement.type == Token.TESTCASE_NAME:
            self.test_name_len = len(statement.data_tokens[0].value) if statement.data_tokens else 0
            self.test_without_eol = statement.tokens[-1].type != Token.EOL
        elif statement.type == Token.TESTCASE_HEADER:
            self.align_header(statement)
        elif not isinstance(
            statement,
            (Comment, EmptyLine, ForHeader, IfHeader, ElseHeader, ElseIfHeader, End),
        ):
            self.align_statement(statement)
        return statement

    def align_header(self, statement):
        tokens = []
        # *** Test Cases ***            baz                            qux
        # *** Test Cases ***      baz         qux
        for index, token in enumerate(statement.data_tokens[:-1]):
            tokens.append(token)
            if self.min_width:
                separator = max(self.formatting_config.space_count, self.min_width - len(token.value)) * " "
            else:
                separator = (self.widths[index] - len(token.value) + self.formatting_config.space_count) * " "
            tokens.append(Token(Token.SEPARATOR, separator))
        tokens.append(statement.data_tokens[-1])
        tokens.append(statement.tokens[-1])  # eol
        statement.tokens = tokens
        return statement

    def align_statement(self, statement):
        tokens = []
        for line in statement.lines:
            strip_line = [t for t in line if t.type not in (Token.SEPARATOR, Token.EOL)]
            line_pos = 0
            exp_pos = 0
            widths = self.get_widths(statement)
            for token, width in zip(strip_line, widths):
                if self.min_width:
                    exp_pos += max(width + self.formatting_config.space_count, self.min_width)
                else:
                    exp_pos += width + self.formatting_config.space_count
                if self.test_without_eol:
                    self.test_without_eol = False
                    exp_pos -= self.test_name_len
                tokens.append(Token(Token.SEPARATOR, (exp_pos - line_pos) * " "))
                tokens.append(token)
                line_pos += len(token.value) + exp_pos - line_pos
            tokens.append(line[-1])
        statement.tokens = tokens

    def get_widths(self, statement):
        indent = self.indent
        if isinstance(statement, (ForHeader, End, IfHeader, ElseHeader, ElseIfHeader)):
            indent -= 1
        if not indent:
            return self.widths
        return [max(width, indent * self.formatting_config.space_count) for width in self.widths]

    def visit_SettingSection(self, node):  # noqa
        return node

    visit_VariableSection = visit_KeywordSection = visit_CommentSection = visit_SettingSection


class ColumnWidthCounter(ModelVisitor):
    def __init__(self, disablers):
        self.widths = []
        self.disablers = disablers
        self.test_name_lineno = -1
        self.any_one_line_test = False
        self.header_with_cols = False

    def visit_TestCaseSection(self, node):  # noqa
        self.generic_visit(node)
        if not self.header_with_cols and not self.any_one_line_test and self.widths:
            self.widths[0] = 0
        self.widths = [misc.round_to_four(length) for length in self.widths]

    def visit_TestCase(self, node):  # noqa
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return
        self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, statement):  # noqa
        if statement.type == Token.COMMENT:
            return
        if statement.type == Token.TESTCASE_HEADER:
            if len(statement.data_tokens) > 1:
                self.header_with_cols = True
                self._count_widths_from_statement(statement)
        elif statement.type == Token.TESTCASE_NAME:
            if self.widths:
                self.widths[0] = max(self.widths[0], len(statement.name))
            else:
                self.widths.append(len(statement.name))
            self.test_name_lineno = statement.lineno
        else:
            if self.test_name_lineno == statement.lineno:
                self.any_one_line_test = True
            if not isinstance(statement, (ForHeader, IfHeader, ElseHeader, ElseIfHeader, End)):
                self._count_widths_from_statement(statement, indent=1)

    def _count_widths_from_statement(self, statement, indent=0):
        for line in statement.lines:
            line = [t for t in line if t.type not in (Token.SEPARATOR, Token.EOL)]
            for index, token in enumerate(line, start=indent):
                if index < len(self.widths):
                    self.widths[index] = max(self.widths[index], len(token.value))
                else:
                    self.widths.append(len(token.value))
