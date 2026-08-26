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

from robocop.exceptions import InvalidParameterValueError
from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc

if TYPE_CHECKING:
    from robot.parsing.model.blocks import File, If, SettingSection, TestCase, TestCaseSection
    from robot.parsing.model.statements import Statement

    from robocop.formatter.disablers import DisablersInFile

UNSET = None

# Statements that represent test case settings (``[Tags]``, ``[Documentation]`` and so on).
SETTING_TYPES = frozenset(
    {
        Token.DOCUMENTATION,
        Token.TAGS,
        Token.SETUP,
        Token.TEARDOWN,
        Token.TEMPLATE,
        Token.TIMEOUT,
    }
)

SPLIT = "split"
SPLIT_ON_SETTINGS = "split_on_settings"
KEEP = "keep"
ARGS_WITH_TEST_MODES = (SPLIT, SPLIT_ON_SETTINGS, KEEP)


def is_setting(statement: Statement) -> bool:
    return bool(getattr(statement, "data_tokens", None)) and statement.data_tokens[0].type in SETTING_TYPES


def is_template_arguments(statement: Statement) -> bool:
    return bool(getattr(statement, "data_tokens", None)) and statement.data_tokens[0].type == Token.ARGUMENT


def has_control_structure(node: TestCase) -> bool:
    """Return ``True`` if the test case contains a block (``FOR``, ``IF``, ``TRY``, ``WHILE``)."""
    # Blocks expose a ``body`` attribute while plain statements do not.
    return any(hasattr(statement, "body") for statement in node.body)


def should_split(node: TestCase, mode: str) -> bool:
    if mode == SPLIT:
        return True
    # ``FOR``/``IF`` blocks break the single-line layout, so they are always split.
    if has_control_structure(node):
        return True
    if mode == SPLIT_ON_SETTINGS:
        return any(is_setting(statement) for statement in node.body)
    return False


class AlignTemplatedTestCases(Formatter):
    """
    Align templated Test Cases to columns.

    The following code:

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
    test1
                            hi          hello
    test2 long test name
                            asdfasdf    asdsdfgsdfg
    ```

    If you don't want to align test case section that does not contain header names (in above example baz and quz are
    header names) then configure `only_with_headers` parameter:

    ```
    robocop format -c AlignSettingsSection.only_with_headers:True <src>
    ```

    Use ``args_with_test`` parameter to control whether template arguments and settings stay in the same line as the
    test case name. Possible values are ``split`` (default), ``split_on_settings`` and ``keep``:

    - ``split`` always moves template arguments and settings to their own line, keeping only the test case name in the
      first line. Test case names are ignored when calculating the column widths (header names are still respected).
    - ``split_on_settings`` moves template arguments and settings to their own line only if the test case contains any
      setting (such as ``[Tags]`` or ``[Documentation]``).
    - ``keep`` keeps template arguments and settings in the same line as the test case name.

    For non-templated test cases use ``AlignTestCasesSection`` formatter.
    """

    ENABLED = False

    def __init__(
        self,
        only_with_headers: bool = False,
        min_width: int | str | None = None,
        args_with_test: str = SPLIT,
    ) -> None:
        super().__init__()
        self.only_with_headers = only_with_headers
        # TODO: Replace Robot importer for formatter with our internal importer (like linter)
        # Robot import will not convert if any of types is None, so we need to do it manually
        self.min_width: int | None = int(min_width) if min_width is not None else None
        self.args_with_test = args_with_test
        self._validate_args_with_test()
        self.widths: list[int] = []
        self.header_with_cols = False
        self.test_name_len = 0
        self.test_without_eol = False
        self.split_current_test = False
        self.indent = 0

    def _validate_args_with_test(self) -> None:
        if self.args_with_test not in ARGS_WITH_TEST_MODES:
            raise InvalidParameterValueError(
                self.__class__.__name__,
                "args_with_test",
                self.args_with_test,
                f"Supported values: {', '.join(ARGS_WITH_TEST_MODES)}.",
            )

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
        self.header_with_cols = len(node.header.data_tokens) > 1
        if not self.header_with_cols and self.only_with_headers:
            return node
        counter = ColumnWidthCounter(self.disablers, self.args_with_test)
        counter.visit(node)
        self.widths = counter.widths
        return self.generic_visit(node)

    def visit_TestCase(self, node: TestCase) -> TestCase:  # noqa: N802
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return node
        self.split_current_test = self.should_split(node)
        self.prepare_test_name_line(node)
        return self.generic_visit(node)

    def should_split(self, node: TestCase) -> bool:
        return should_split(node, self.args_with_test)

    def prepare_test_name_line(self, node: TestCase) -> None:
        """Decide which statement (if any) stays in the same line as the test case name and update the name eol."""
        header = node.header
        name_token = header.data_tokens[0]
        self.test_name_len = len(name_token.value)
        on_name_line = self.get_statement_on_name_line(node)
        self.test_without_eol = on_name_line is not None
        if on_name_line is not None:
            header.tokens = [name_token]
        else:
            header.tokens = [name_token, Token(Token.EOL)]

    def get_statement_on_name_line(self, node: TestCase) -> Statement | None:
        if self.split_current_test:
            return None
        first_statement = self.first_body_statement(node)
        if first_statement is None:
            return None
        if first_statement.lineno == node.header.lineno:
            return first_statement
        # ``keep`` pulls the first body row (template arguments or a setting) up to the name line when header names
        # are present.
        if (
            self.args_with_test == KEEP
            and self.header_with_cols
            and (is_template_arguments(first_statement) or is_setting(first_statement))
        ):
            return first_statement
        return None

    @staticmethod
    def first_body_statement(node: TestCase) -> Statement | None:
        for statement in node.body:
            if not isinstance(statement, EmptyLine):
                return statement
        return None

    @skip_if_disabled
    def visit_Statement(self, statement: Statement) -> Statement:  # noqa: N802
        if statement.type == Token.TESTCASE_NAME:
            return statement
        if statement.type == Token.TESTCASE_HEADER:
            self.align_header(statement)
        elif self.split_current_test and is_setting(statement):
            self.align_indented(statement)
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
                separator = max(self.formatting_config.space_count, self.min_width - len(token.value)) * " "
            else:
                separator = (self.widths[index] - len(token.value) + self.formatting_config.space_count) * " "
            tokens.append(Token(Token.SEPARATOR, separator))
        tokens.append(statement.data_tokens[-1])
        tokens.append(statement.tokens[-1])  # eol
        statement.tokens = tokens
        return statement

    def align_indented(self, statement: Statement) -> None:
        """Align a statement using a fixed indentation instead of the column widths (used for split settings)."""
        space_count = self.formatting_config.space_count
        indent = (self.indent + 1) * space_count * " "
        separator = space_count * " "
        tokens = []
        for line in statement.lines:
            strip_line = [token for token in line if token.type not in (Token.SEPARATOR, Token.EOL)]
            for index, token in enumerate(strip_line):
                tokens.append(Token(Token.SEPARATOR, indent if index == 0 else separator))
                tokens.append(token)
            tokens.append(line[-1])
        statement.tokens = tokens

    def align_statement(self, statement: Statement) -> None:
        tokens = []
        for line in statement.lines:
            strip_line = [t for t in line if t.type not in (Token.SEPARATOR, Token.EOL)]
            line_pos = 0
            exp_pos = 0
            widths = self.get_widths(statement)
            for token, width in zip(strip_line, widths, strict=False):
                if self.min_width:
                    exp_pos += max(width + self.formatting_config.space_count, self.min_width)
                else:
                    exp_pos += width + self.formatting_config.space_count
                if self.test_without_eol:
                    self.test_without_eol = False
                    exp_pos -= self.test_name_len
                sep_len = max(exp_pos - line_pos, self.formatting_config.space_count)
                tokens.append(Token(Token.SEPARATOR, sep_len * " "))
                tokens.append(token)
                line_pos += len(token.value) + exp_pos - line_pos
            tokens.append(line[-1])
        statement.tokens = tokens

    def get_widths(self, statement: Statement) -> list[int]:
        indent = self.indent
        if isinstance(statement, (ForHeader, End, IfHeader, ElseHeader, ElseIfHeader)):
            indent -= 1
        if not indent:
            return self.widths
        return [max(width, indent * self.formatting_config.space_count) for width in self.widths]

    def visit_SettingSection(self, node: SettingSection) -> SettingSection:  # noqa: N802
        return node

    visit_VariableSection = visit_KeywordSection = visit_CommentSection = visit_SettingSection  # noqa: N815


class ColumnWidthCounter(ModelVisitor):  # type: ignore[misc]
    def __init__(self, disablers: DisablersInFile, args_with_test: str) -> None:
        self.widths: list[int] = []
        self.disablers: DisablersInFile = disablers
        self.args_with_test = args_with_test
        self.split_current_test = False
        self.test_name_lineno: int = -1
        self.any_one_line_test: bool = False
        self.header_with_cols: bool = False

    def visit_TestCaseSection(self, node: TestCaseSection) -> None:  # noqa: N802
        self.generic_visit(node)
        if not self.header_with_cols and not self.any_one_line_test and self.widths:
            self.widths[0] = 0

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        for statement in node.body:
            if isinstance(statement, Template) and statement.value is None:
                return
        self.split_current_test = should_split(node, self.args_with_test)
        self.generic_visit(node)

    @skip_if_disabled
    def visit_Statement(self, statement: Statement) -> None:  # noqa: N802
        if statement.type in (Token.COMMENT, Token.DOCUMENTATION):
            return
        if statement.type == Token.TESTCASE_HEADER:
            if len(statement.data_tokens) > 1:
                self.header_with_cols = True
                self._count_widths_from_statement(statement)
        elif statement.type == Token.TESTCASE_NAME:
            # Split test case names are moved to their own line, so they don't count towards the column widths.
            name_len = 0 if self.split_current_test else len(statement.name)
            if self.widths:
                self.widths[0] = max(self.widths[0], name_len)
            else:
                self.widths.append(name_len)
            self.test_name_lineno = statement.lineno
        else:
            if not self.split_current_test and self.test_name_lineno == statement.lineno:
                self.any_one_line_test = True
            # Settings are aligned to columns only when they stay in place (i.e. the test case is not split).
            if self.split_current_test and is_setting(statement):
                return
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
