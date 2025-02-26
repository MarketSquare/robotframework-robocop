from robot.api.parsing import Token

try:
    from robot.api.parsing import InlineIfHeader, ReturnStatement
except ImportError:
    InlineIfHeader = None
    ReturnStatement = None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.skip import Skip
from robocop.formatter.utils.misc import join_comments


class NormalizeSeparators(Formatter):
    """
    Normalize separators and indents.

    All separators (pipes included) are converted to fixed length of 4 spaces (configurable via global argument
    ``--spacecount``).

    To not format documentation configure ``skip_documentation`` to ``True``.
    """

    HANDLES_SKIP = frozenset(
        {
            "skip_documentation",
            "skip_keyword_call",
            "skip_keyword_call_pattern",
            "skip_comments",
            "skip_block_comments",
            "skip_sections",
        }
    )

    def __init__(self, flatten_lines: bool = False, align_new_line: bool = False, skip: Skip = None):
        super().__init__(skip=skip)
        self.indent = 0
        self.flatten_lines = flatten_lines
        self.is_inline = False
        self.align_new_line = align_new_line
        self._allowed_line_length = None  # we can only retrieve it after all formatters are initialized

    @property
    def allowed_line_length(self) -> int:
        """Get line length from SplitTooLongLine formatter or global config."""
        if self._allowed_line_length is None:
            if "SplitTooLongLine" in self.formatters:
                self._allowed_line_length = self.formatters["SplitTooLongLine"].line_length
            else:
                self._allowed_line_length = self.formatting_config.line_length
        return self._allowed_line_length

    def visit_File(self, node):  # noqa: N802
        self.indent = 0
        return self.generic_visit(node)

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    def indented_block(self, node):
        self.visit_Statement(node.header)
        self.indent += 1
        node.body = [self.visit(item) for item in node.body]
        self.indent -= 1
        return node

    def visit_TestCase(self, node):  # noqa: N802
        return self.indented_block(node)

    visit_Keyword = visit_While = visit_TestCase  # noqa: N815

    def visit_For(self, node):  # noqa: N802
        node = self.indented_block(node)
        self.visit_Statement(node.end)
        return node

    def visit_Try(self, node):  # noqa: N802
        node = self.indented_block(node)
        if node.next:
            self.visit(node.next)
        if node.end:
            self.visit_Statement(node.end)
        return node

    def visit_If(self, node):  # noqa: N802
        if self.is_inline and InlineIfHeader and isinstance(node.header, InlineIfHeader):  # nested inline if is ignored
            return node
        self.is_inline = self.is_inline or (InlineIfHeader and isinstance(node.header, InlineIfHeader))
        self.visit_Statement(node.header)
        self.indent += 1
        node.body = [self.visit(item) for item in node.body]
        self.indent -= 1
        if node.orelse:
            self.visit_If(node.orelse)
        if node.end:
            self.visit_Statement(node.end)
        self.is_inline = False
        return node

    @skip_if_disabled
    def visit_Documentation(self, doc):  # noqa: N802
        if self.skip.documentation or self.flatten_lines:
            has_pipes = doc.tokens[0].value.startswith("|")
            return self.handle_spaces(doc, has_pipes, only_indent=True)
        return self.visit_Statement(doc)

    def visit_KeywordCall(self, keyword):  # noqa: N802
        if self.skip.keyword_call(keyword):
            return keyword
        return self.visit_Statement(keyword)

    @skip_if_disabled
    def visit_Comment(self, node):  # noqa: N802
        if self.skip.comment(node):
            return node
        has_pipes = node.tokens[0].value.startswith("|")
        return self.handle_spaces(node, has_pipes)

    def is_keyword_inside_inline_if(self, node):
        return self.is_inline and not isinstance(node, InlineIfHeader)

    @skip_if_disabled
    def visit_Statement(self, statement):  # noqa: N802
        if statement is None:
            return None
        has_pipes = statement.tokens[0].value.startswith("|")
        if has_pipes or not self.flatten_lines:
            return self.handle_spaces(statement, has_pipes)
        return self.handle_spaces_and_flatten_lines(statement)

    @staticmethod
    def has_trailing_sep(tokens):
        return tokens and tokens[-1].type == Token.SEPARATOR

    def handle_spaces_and_flatten_lines(self, statement):
        """Normalize separators and flatten multiline statements to one line."""
        add_eol, prev_sep = False, False
        add_indent = not self.is_keyword_inside_inline_if(statement)
        new_tokens, comments = [], []
        for token in statement.tokens:
            if token.type == Token.SEPARATOR:
                if prev_sep:
                    continue
                prev_sep = True
                if add_indent:
                    token.value = self.formatting_config.indent * self.indent
                else:
                    token.value = self.formatting_config.separator
            elif token.type == Token.EOL:
                add_eol = True
                continue
            elif token.type == Token.CONTINUATION:
                continue
            elif token.type == Token.COMMENT:
                comments.append(token)
                continue
            else:
                prev_sep = False
            new_tokens.append(token)
            add_indent = False
        if not self.is_inline and self.has_trailing_sep(new_tokens):
            new_tokens.pop()
        if comments:
            joined_comments = join_comments(comments)
            if self.has_trailing_sep(new_tokens):
                joined_comments = joined_comments[1:]
            new_tokens.extend(joined_comments)
        if add_eol:
            new_tokens.append(Token(Token.EOL))
        statement.tokens = new_tokens
        self.generic_visit(statement)
        return statement

    def handle_spaces(self, statement, has_pipes, only_indent=False):
        new_tokens = []
        prev_token = None
        first_col_width = 0
        first_data_token = True
        is_sep_after_first_data_token = False
        align_continuation = self.align_new_line
        for line in statement.lines:
            prev_sep = False
            line_length = 0
            for index, token in enumerate(line):
                if token.type == Token.SEPARATOR:
                    if prev_sep:
                        continue
                    prev_sep = True
                    if index == 0 and not self.is_keyword_inside_inline_if(statement):
                        token.value = self.formatting_config.indent * self.indent
                    elif not only_indent:
                        if prev_token and prev_token.type == Token.CONTINUATION:
                            if align_continuation:
                                token.value = first_col_width * " "
                            else:
                                token.value = self.formatting_config.continuation_indent
                        else:
                            token.value = self.formatting_config.separator
                else:
                    prev_sep = False
                    if align_continuation:
                        if first_data_token:
                            first_col_width += max(len(token.value), 3) - 3  # remove ... token length
                            # Check if first line is not longer than allowed line length - we can't align over limit
                            align_continuation = align_continuation and first_col_width < self.allowed_line_length
                            first_data_token = False
                        elif not is_sep_after_first_data_token and token.type != Token.EOL:
                            is_sep_after_first_data_token = True
                            first_col_width += len(self.formatting_config.separator)
                    prev_token = token
                if has_pipes and index == len(line) - 2:
                    token.value = token.value.rstrip()
                line_length += len(token.value)
                new_tokens.append(token)
        statement.tokens = new_tokens
        self.generic_visit(statement)
        return statement
