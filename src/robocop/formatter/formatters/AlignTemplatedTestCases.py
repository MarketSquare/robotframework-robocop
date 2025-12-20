from __future__ import annotations

from typing import TYPE_CHECKING

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

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc

if TYPE_CHECKING:
    from robot.parsing.model.blocks import File, If, TestCase, TestCaseSection
    from robot.parsing.model.statements import Statement

    from robocop.formatter.disablers import DisablersInFile


class AlignTemplatedTestCases(Formatter):
    """
    Align templated Test Cases to columns.

    Following code:

    ```robotframework
    *** Test Cases ***    baz    qux
    # some comment
    test1    hi    hello
    test2 long test name    asdfasdf    asdsdfgsdfg
    ```

    will be formatted to:

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
    robocop format -c AlignSettingsSection.only_with_headers:True <src>
    ```

    For non-templated test cases use ``AlignTestCasesSection`` formatter.
    """

    ENABLED = False

    def __init__(self, only_with_headers: bool = False, min_width: int | str | None = None):
        super().__init__()
        self.only_with_headers = only_with_headers
        # Convert min_width to int if it's a string (from CLI config)
        self.min_width: int | None = int(min_width) if min_width is not None else None
        self.widths: list[int] | None = None
        self.test_name_len: int = 0
        self.test_without_eol: bool = False
        self.indent: int = 0

    def visit_File(self, node: File) -> File:  # noqa: N802
        if not misc.is_suite_templated(node):
            return node
        self.test_without_eol = False
        return self.generic_visit(node)

    def visit_If(self, node: If) -> If:  # noqa: N802
        self.indent += 1
        self.generic_visit(node)
        self.indent -= 1
        return node

    visit_Else = visit_ElseIf = visit_For = visit_If  # noqa: N815

    @skip_section_if_disabled
    def visit_TestCaseSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        if len(node.header.data_tokens) == 1 and self.only_with_headers:
            return node
        counter = ColumnWidthCounter(self.disablers)
        counter.visit(node)
        self.widths = counter.widths
        return self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> TestCase:  # noqa: N802
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return node
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, statement: Statement) -> Statement:  # noqa: N802
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

    def align_header(self, statement: Statement) -> Statement:
        tokens = []
        # *** Test Cases ***            baz                            qux
        # *** Test Cases ***      baz         qux
        for index, token in enumerate(statement.data_tokens[:-1]):
            tokens.append(token)
            if self.min_width:
                separator = max(int(self.formatting_config.space_count), self.min_width - len(token.value)) * " "  # type: ignore[union-attr,arg-type]
            else:
                separator = (self.widths[index] - len(token.value) + int(self.formatting_config.space_count)) * " "  # type: ignore[union-attr,arg-type,index,operator]
            tokens.append(Token(Token.SEPARATOR, separator))
        tokens.append(statement.data_tokens[-1])
        tokens.append(statement.tokens[-1])  # eol
        statement.tokens = tokens
        return statement

    def align_statement(self, statement: Statement) -> None:
        tokens = []
        for line in statement.lines:
            strip_line = [t for t in line if t.type not in (Token.SEPARATOR, Token.EOL)]
            line_pos = 0
            exp_pos = 0
            widths = self.get_widths(statement)
            for token, width in zip(strip_line, widths, strict=False):
                if self.min_width:
                    exp_pos += max(width + int(self.formatting_config.space_count), self.min_width)  # type: ignore[union-attr,arg-type]
                else:
                    exp_pos += width + int(self.formatting_config.space_count)  # type: ignore[union-attr,arg-type]
                if self.test_without_eol:
                    self.test_without_eol = False
                    exp_pos -= self.test_name_len
                tokens.append(Token(Token.SEPARATOR, (exp_pos - line_pos) * " "))
                tokens.append(token)
                line_pos += len(token.value) + exp_pos - line_pos
            tokens.append(line[-1])
        statement.tokens = tokens

    def get_widths(self, statement: Statement) -> list[int]:
        indent = self.indent
        if isinstance(statement, (ForHeader, End, IfHeader, ElseHeader, ElseIfHeader)):
            indent -= 1
        if not indent:
            return self.widths  # type: ignore[return-value]
        return [max(width, indent * int(self.formatting_config.space_count)) for width in self.widths]  # type: ignore[union-attr,arg-type]

    def visit_SettingSection(self, node: TestCaseSection) -> TestCaseSection:  # noqa: N802
        return node

    visit_VariableSection = visit_KeywordSection = visit_CommentSection = visit_SettingSection  # noqa: N815


class ColumnWidthCounter(ModelVisitor):  # type: ignore[misc]
    def __init__(self, disablers: DisablersInFile | None):
        self.widths: list[int] = []
        self.disablers: DisablersInFile | None = disablers
        self.test_name_lineno: int = -1
        self.any_one_line_test: bool = False
        self.header_with_cols: bool = False

    def visit_TestCaseSection(self, node: TestCaseSection) -> None:  # noqa: N802
        self.generic_visit(node)
        if not self.header_with_cols and not self.any_one_line_test and self.widths:
            self.widths[0] = 0
        self.widths = [misc.round_to_four(length) for length in self.widths]

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return
        self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, statement: Statement) -> None:  # noqa: N802
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

    def _count_widths_from_statement(self, statement: Statement, indent: int = 0) -> None:
        for line in statement.lines:
            line = [t for t in line if t.type not in (Token.SEPARATOR, Token.EOL)]
            for index, token in enumerate(line, start=indent):
                if index < len(self.widths):
                    self.widths[index] = max(self.widths[index], len(token.value))
                else:
                    self.widths.append(len(token.value))
