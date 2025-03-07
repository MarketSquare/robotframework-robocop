from itertools import chain

from robot.api.parsing import Comment, ElseHeader, ElseIfHeader, End, If, IfHeader, KeywordCall, Token

try:
    from robot.api.parsing import Break, Continue, InlineIfHeader, ReturnStatement
except ImportError:
    ReturnStatement, Break, Continue, InlineIfHeader = None, None, None, None

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.formatters import Formatter
from robocop.formatter.utils import misc


class InlineIf(Formatter):
    """
    Replaces IF blocks with inline IF.

    It will only replace IF block if it can fit in one line shorter than `line_length` (default 80) parameter and return
    variables matches for all ELSE and ELSE IF branches.

    Following code:

    ```robotframework
    *** Test Cases ***
    Test
        IF    $condition1
            Keyword    argument
        END
        IF    $condition2
            ${var}  Keyword
        ELSE
            ${var}  Keyword 2
        END
        IF    $condition1
            Keyword    argument
            Keyword 2
        END
    ```

    will be formatted to:

    ```robotframework
    *** Test Cases ***
    Test
        IF    $condition1    Keyword    argument
        ${var}    IF    $condition2    Keyword    ELSE    Keyword 2
        IF    $condition1
            Keyword    argument
            Keyword 2
        END
    ```

    Too long inline IFs (over `line_length` character limit) will be replaced with normal IF block.
    You can decide to not replace IF blocks containing ELSE or ELSE IF branches by setting `skip_else` to True.

    """

    MIN_VERSION = 5

    def __init__(self, line_length: int = 80, skip_else: bool = False):
        super().__init__()
        self.line_length = line_length
        self.skip_else = skip_else

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    def visit_If(self, node: If):  # noqa: N802
        if node.errors or getattr(node.end, "errors", None):
            return node
        if self.disablers.is_node_disabled("InlineIf", node, full_match=False):
            return node
        if self.is_inline(node):
            return self.handle_inline(node)
        self.generic_visit(node)
        if self.no_end(node):
            return node
        indent = node.header.tokens[0]
        if not (self.should_format(node) and self.assignment_identical(node)):
            return node
        return self.to_inline(node, indent.value)

    def should_format(self, node):
        if node.header.errors:
            return False
        if (
            len(node.body) > 1
            or not node.body
            or not isinstance(node.body[0], (KeywordCall, ReturnStatement, Break, Continue))
        ):
            return False
        if node.orelse:
            return self.should_format(node.orelse)
        return True

    @staticmethod
    def if_to_branches(if_block):
        while if_block:
            yield if_block
            if_block = if_block.orelse

    def assignment_identical(self, node):
        else_found = False
        assigned = []
        for branch in self.if_to_branches(node):
            if isinstance(branch.header, ElseHeader):
                else_found = True
            if not isinstance(branch.body[0], KeywordCall) or not branch.body[0].assign:
                assigned.append([])
            else:
                assigned.append([misc.normalize_name(assign).replace("=", "") for assign in branch.body[0].assign])
            if len(assigned) > 1 and assigned[-1] != assigned[-2]:
                return False
        if any(x for x in assigned):
            return else_found
        return True

    def is_shorter_than_limit(self, inline_if):
        line_len = sum(self.if_len(branch) for branch in self.if_to_branches(inline_if))
        return line_len <= self.line_length

    @staticmethod
    def no_end(node):
        if not node.end:
            return True
        if len(node.end.tokens) != 1:
            return False
        return not node.end.tokens[0].value

    @staticmethod
    def is_inline(node):
        return isinstance(node.header, InlineIfHeader)

    @staticmethod
    def if_len(if_st):
        return sum(
            len(tok.value)
            for tok in chain(if_st.body[0].tokens if if_st.body else [], if_st.header.tokens)
            if tok.value != "\n"
        )

    def to_inline(self, node, indent):
        tail = node
        comments = self.collect_comments_from_if(indent, node)
        if_block = head = self.inline_if_from_branch(node, indent)
        while tail.orelse:
            if self.skip_else:
                return node
            tail = tail.orelse
            comments += self.collect_comments_from_if(indent, tail)
            head.orelse = self.inline_if_from_branch(tail, self.formatting_config.separator)
            head = head.orelse
        if self.is_shorter_than_limit(if_block):
            return (*comments, if_block)
        return node

    def inline_if_from_branch(self, node, indent):
        if not node:
            return None
        separator = self.formatting_config.separator
        last_token = Token(Token.EOL) if node.orelse is None else Token(Token.SEPARATOR, separator)
        assigned = None

        if isinstance(node.body[0], KeywordCall):
            assigned = node.body[0].assign
            keyword = self.to_inline_keyword(node.body[0], separator, last_token)
        elif isinstance(node.body[0], ReturnStatement):
            keyword = self.to_inline_return(node.body[0], separator, last_token)
        elif isinstance(node.body[0], Break):
            keyword = Break(self.to_inline_break_continue_tokens(Token.BREAK, separator, last_token))
        elif isinstance(node.body[0], Continue):
            keyword = Continue(self.to_inline_break_continue_tokens(Token.CONTINUE, separator, last_token))
        else:
            return node

        # check for ElseIfHeader first since it's child of IfHeader class
        if isinstance(node.header, ElseIfHeader):
            header = ElseIfHeader(
                [Token(Token.ELSE_IF), Token(Token.SEPARATOR, separator), Token(Token.ARGUMENT, node.header.condition)]
            )
        elif isinstance(node.header, IfHeader):
            tokens = [Token(Token.SEPARATOR, indent)]
            if assigned:
                for assign in assigned:
                    tokens.extend([Token(Token.ASSIGN, assign), Token(Token.SEPARATOR, separator)])
            tokens.extend(
                [
                    Token(Token.INLINE_IF),
                    Token(Token.SEPARATOR, separator),
                    Token(Token.ARGUMENT, node.header.condition),
                ]
            )
            header = InlineIfHeader(tokens)
        elif isinstance(node.header, ElseHeader):
            header = ElseHeader([Token(Token.ELSE)])
        else:
            return node
        return If(header=header, body=[keyword])

    @staticmethod
    def to_inline_keyword(keyword, separator, last_token):
        tokens = [Token(Token.SEPARATOR, separator), Token(Token.KEYWORD, keyword.keyword)]
        for arg in keyword.get_tokens(Token.ARGUMENT):
            tokens.extend([Token(Token.SEPARATOR, separator), arg])
        tokens.append(last_token)
        return KeywordCall(tokens)

    @staticmethod
    def to_inline_return(node, separator, last_token):
        tokens = [Token(Token.SEPARATOR, separator), Token(Token.RETURN_STATEMENT)]
        for value in node.values:
            tokens.extend([Token(Token.SEPARATOR, separator), Token(Token.ARGUMENT, value)])
        tokens.append(last_token)
        return ReturnStatement(tokens)

    @staticmethod
    def to_inline_break_continue_tokens(token, separator, last_token):
        return [Token(Token.SEPARATOR, separator), Token(token), last_token]

    @staticmethod
    def join_on_separator(tokens, separator):
        for token in tokens:
            yield token
            yield separator

    @staticmethod
    def collect_comments_from_if(indent, node):
        comments = misc.get_comments(node.header.tokens)
        for statement in node.body:
            comments += misc.get_comments(statement.tokens)
        if node.end:
            comments += misc.get_comments(node.end)
        return [Comment.from_params(comment=comment.value, indent=indent) for comment in comments]

    def create_keyword_for_inline(self, kw_tokens, indent, assign):
        keyword_tokens = []
        for token in kw_tokens:
            keyword_tokens.append(Token(Token.SEPARATOR, self.formatting_config.separator))
            keyword_tokens.append(token)
        return KeywordCall.from_tokens(
            [
                Token(Token.SEPARATOR, indent + self.formatting_config.separator),
                *assign,
                *keyword_tokens[1:],
                Token(Token.EOL),
            ]
        )

    def flatten_if_block(self, node):
        node.header.tokens = misc.flatten_multiline(
            node.header.tokens, self.formatting_config.separator, remove_comments=True
        )
        for index, statement in enumerate(node.body):
            node.body[index].tokens = misc.flatten_multiline(
                statement.tokens, self.formatting_config.separator, remove_comments=True
            )
        return node

    def is_if_multiline(self, node):
        for branch in self.if_to_branches(node):
            if branch.header.get_token(Token.CONTINUATION):
                return True
            if any(statement.get_token(Token.CONTINUATION) for statement in branch.body):
                return True
        return False

    def flatten_inline_if(self, node):
        indent = node.header.tokens[0].value
        comments = self.collect_comments_from_if(indent, node)
        node = self.flatten_if_block(node)
        head = node
        while head.orelse:
            head = head.orelse
            comments += self.collect_comments_from_if(indent, head)
            head = self.flatten_if_block(head)
        return comments, node

    def handle_inline(self, node):
        if self.is_if_multiline(node):
            comments, node = self.flatten_inline_if(node)
        else:
            comments = []
        if self.is_shorter_than_limit(node):  # TODO ignore comments?
            return (*comments, node)
        indent = node.header.tokens[0]
        separator = self.formatting_config.separator
        assign_tokens = node.header.get_tokens(Token.ASSIGN)
        assign = [*self.join_on_separator(assign_tokens, Token(Token.SEPARATOR, separator))]
        else_present = False
        branches = []
        while node:
            new_comments, if_block, else_found = self.handle_inline_if_create(node, indent.value, assign)
            else_present = else_present or else_found
            comments += new_comments
            branches.append(if_block)
            node = node.orelse
        if not else_present and assign_tokens:
            header = ElseHeader.from_params(indent=indent.value)
            keyword = self.create_keyword_for_inline(
                [
                    Token(Token.KEYWORD, "Set Variable"),
                    *[Token(Token.ARGUMENT, "${None}") for _ in range(len(assign_tokens))],
                ],
                indent.value,
                assign,
            )
            branches.append(If(header=header, body=[keyword]))
        if_block = head = branches[0]
        for branch in branches[1:]:
            head.orelse = branch
            head = head.orelse
        if_block.end = End([indent, Token(Token.END), Token(Token.EOL)])
        return (*comments, if_block)

    def handle_inline_if_create(self, node, indent, assign):
        comments = self.collect_comments_from_if(indent, node)
        body = [self.create_keyword_for_inline(node.body[0].data_tokens, indent, assign)]
        else_found = False
        if isinstance(node.header, InlineIfHeader):
            header = IfHeader.from_params(
                condition=node.condition, indent=indent, separator=self.formatting_config.separator
            )
        elif isinstance(node.header, ElseIfHeader):
            header = ElseIfHeader.from_params(
                condition=node.condition, indent=indent, separator=self.formatting_config.separator
            )
        else:
            header = ElseHeader.from_params(indent=indent)
            else_found = True
        return comments, If(header=header, body=body), else_found
