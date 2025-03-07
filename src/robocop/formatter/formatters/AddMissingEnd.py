from robot.api.parsing import Comment, EmptyLine, End, Token

try:
    from robot.api.parsing import InlineIfHeader
except ImportError:
    InlineIfHeader = None

from robocop.formatter.disablers import skip_if_disabled, skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.skip import Skip


class AddMissingEnd(Formatter):
    """
    Add missing END token to FOR loops and IF statements.

    Following code:

    ```robotframework
    *** Keywords ***
    Keyword
        FOR    ${x}    IN    foo    bar
            Log    ${x}
    ```

    will be formatted to:

    ```robotframework
    *** Keywords ***
    Keyword
        FOR    ${x}    IN    foo    bar
            Log    ${x}
        END
    ```
    """

    HANDLES_SKIP = frozenset({"skip_sections"})

    def __init__(self, skip: Skip = None):
        super().__init__(skip)

    def fix_block(self, node, expected_type):
        self.generic_visit(node)
        self.fix_header_name(node, expected_type)
        outside = []
        if not node.end:  # fix statement position only if END was missing
            node.body, outside = self.collect_inside_statements(node)
        self.fix_end(node)
        return (node, *outside)

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    @skip_if_disabled
    def visit_For(self, node):  # noqa: N802
        return self.fix_block(node, Token.FOR)

    @skip_if_disabled
    def visit_While(self, node):  # noqa: N802
        return self.fix_block(node, Token.WHILE)

    @skip_if_disabled
    def visit_Try(self, node):  # noqa: N802
        self.generic_visit(node)
        if node.type != Token.TRY:
            return node
        self.fix_header_name(node, node.type)
        outside = []
        if not node.end:  # fix statement position only if END was missing
            node.body, outside = self.collect_inside_statements(node)
            try_branch = self.get_last_except(node)
            if try_branch:
                try_branch.body, outside_try = self.collect_inside_statements(try_branch)
                outside += outside_try

        self.fix_end(node)
        return (node, *outside)

    @skip_if_disabled
    def visit_If(self, node):  # noqa: N802
        self.generic_visit(node)
        if node.type != Token.IF:
            return node
        if InlineIfHeader and isinstance(node.header, InlineIfHeader):
            self.fix_header_name(node, "IF")
            return node
        self.fix_header_name(node, node.type)
        outside = []
        if not node.end:
            node.body, outside = self.collect_inside_statements(node)
            or_else = self.get_last_or_else(node)
            if or_else:
                or_else.body, outside_or_else = self.collect_inside_statements(or_else)
                outside += outside_or_else

        self.fix_end(node)
        return (node, *outside)

    def fix_end(self, node):
        """Fix END (missing END, End -> END, END position should be the same as FOR etc)."""
        if node.header.tokens[0].type == Token.SEPARATOR:
            indent = node.header.tokens[0]
        else:
            indent = Token(Token.SEPARATOR, self.formatting_config.separator)
        node.end = End([indent, Token(Token.END, Token.END), Token(Token.EOL)])

    @staticmethod
    def fix_header_name(node, header_name):
        node.header.data_tokens[0].value = header_name

    def collect_inside_statements(self, node):
        """
        Split statements from node for those that belong to it and outside nodes.

        In this example with missing END:
            FOR  ${i}  IN RANGE  10
                Keyword
            Other Keyword

        RF will store 'Other Keyword' inside FOR block even if it should be outside.
        """
        new_body = [[], []]
        is_outside = False
        starting_col = self.get_column(node)
        for child in node.body:
            if not isinstance(child, EmptyLine) and self.get_column(child) <= starting_col:
                is_outside = True
            new_body[is_outside].append(child)
        while new_body[0] and isinstance(new_body[0][-1], EmptyLine):
            new_body[1].insert(0, new_body[0].pop())
        return new_body

    @staticmethod
    def get_column(node):
        if hasattr(node, "header"):
            return node.header.data_tokens[0].col_offset
        if isinstance(node, Comment):
            token = node.get_token(Token.COMMENT)
            return token.col_offset
        if not node.data_tokens:
            return node.col_offset
        return node.data_tokens[0].col_offset

    @staticmethod
    def get_last_or_else(node):
        if not node.orelse:
            return None
        or_else = node.orelse
        while or_else.orelse:
            or_else = or_else.orelse
        return or_else

    @staticmethod
    def get_last_except(node):
        if not node.next:
            return None
        try_branch = node.next
        while try_branch.next:
            try_branch = try_branch.next
        return try_branch
