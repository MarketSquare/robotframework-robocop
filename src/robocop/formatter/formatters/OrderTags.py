from robot.api.parsing import Token

from robocop.formatter.disablers import skip_section_if_disabled
from robocop.formatter.formatters import Formatter


class OrderTags(Formatter):
    """
    Order tags.

    Tags are ordered in lexicographic order like this:

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        My Keyword

    *** Keywords ***
    My Keyword
        [Tags]    ba    Ab    Bb    Ca    Cb    aa
        No Operation
    ```

    To:

    ```robotframework
    *** Test Cases ***
    Tags Upper Lower
        [Tags]    aa    Ab    ba    Bb    Ca    Cb
        My Keyword

    *** Keywords ***
    My Keyword
        [Tags]    aa    Ab    ba    Bb    Ca    Cb
        No Operation
    ```

    Default order can be changed using following parameters:
      - ``case_sensitive = False``
      - ``reverse = False``
    """

    ENABLED = False

    def __init__(
        self,
        case_sensitive: bool = False,
        reverse: bool = False,
        default_tags: bool = True,
        force_tags: bool = True,
    ):
        super().__init__()
        self.key = self.get_key(case_sensitive)
        self.reverse = reverse
        self.default_tags = default_tags
        self.force_tags = force_tags

    @skip_section_if_disabled
    def visit_Section(self, node):  # noqa: N802
        return self.generic_visit(node)

    def visit_Tags(self, node):  # noqa: N802
        return self.order_tags(node, indent=True)

    def visit_DefaultTags(self, node):  # noqa: N802
        return self.order_tags(node) if self.default_tags else node

    def visit_ForceTags(self, node):  # noqa: N802
        return self.order_tags(node) if self.force_tags else node

    def order_tags(self, node, indent=False):
        if self.disablers.is_node_disabled("OrderTags", node):
            return node
        ordered_tags = sorted(
            (tag.value for tag in node.data_tokens[1:]),
            key=self.key,
            reverse=self.reverse,
        )
        if len(ordered_tags) <= 1:
            return node
        comments = node.get_tokens(Token.COMMENT)
        tokens = []
        if indent:
            tokens.append(Token(Token.SEPARATOR, self.formatting_config.indent))
        tokens.append(node.data_tokens[0])
        tag_tokens = (Token(Token.ARGUMENT, tag) for tag in ordered_tags)
        tokens.extend(self.join_tokens(tag_tokens))
        tokens.extend(self.join_tokens(comments))
        tokens.append(Token(Token.EOL))
        node.tokens = tokens
        return node

    def join_tokens(self, tokens):
        joined_tokens = []
        separator = Token(Token.SEPARATOR, self.formatting_config.separator)
        for token in tokens:
            joined_tokens.append(separator)
            joined_tokens.append(token)
        return joined_tokens

    @staticmethod
    def get_key(case_sensitive):
        return str if case_sensitive else str.casefold
