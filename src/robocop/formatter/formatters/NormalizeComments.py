from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api.parsing import Token

from robocop.formatter.formatters import Formatter

if TYPE_CHECKING:
    from robot.parsing.model.statements import Comment, Statement


class NormalizeComments(Formatter):
    """
    Normalize comments.

    Normalizes spacing after beginning of the comment. Fixes ``missing-space-after-comment`` rule violations
    from the Robocop.

    Following code:

    ```robotframework
    *** Settings ***
    #linecomment
    ### header


    *** Keywords ***
    Keyword
        Step  #comment
    ```

    will be formatted to:

    ```robotframework
    *** Settings ***
    # linecomment
    ### header


    *** Keywords ***
    Keyword
        Step  # comment
    ```
    """

    HANDLES_SKIP = frozenset(
        {
            "skip_comments",
            "skip_block_comments",
        }
    )

    def visit_Comment(self, node: Comment) -> Comment:  # noqa: N802
        return self.handle_comments(node)

    def visit_Statement(self, node: Statement) -> Statement:  # noqa: N802
        return self.handle_comments(node)

    def handle_comments(self, node: Comment | Statement) -> Comment | Statement:
        if self.skip.comment(node):
            return node
        for line in node.lines:
            for token in line:
                if token.type == Token.COMMENT:
                    self.fix_comment_spacing(token)
                    break  # ignore other comments in the same line
        return node

    @staticmethod
    def fix_comment_spacing(comment: Token) -> None:
        # for example content of whole *** Comments *** does not require #
        if len(comment.value) == 1 or not comment.value.startswith("#"):
            return
        if comment.value[1] not in (" ", "#"):
            comment.value = f"# {comment.value[1:]}"
