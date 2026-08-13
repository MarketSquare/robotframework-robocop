"""Checkers for the rules defined in ``robocop.linter.rules.comments``."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, ClassVar

from robot.api import Token
from robot.parsing.model.statements import Documentation

from robocop.linter.rules import VisitorChecker, comments
from robocop.linter.rules.comments import get_line_tokens
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from robot.parsing.model import Keyword, Statement, TestCase
    from robot.parsing.model.blocks import CommentSection
    from robot.parsing.model.statements import Comment


class CommentChecker(VisitorChecker):
    """Checker for comments content. It detects invalid comments or leftovers like `todo` or `fixme` in the code."""

    todo_in_comment: comments.ToDoInCommentRule
    missing_space_after_comment: comments.MissingSpaceAfterCommentRule
    invalid_comment: comments.InvalidCommentRule
    commented_out_code: comments.CommentedOutCodeRule

    # Token types that indicate RF code in keyword context (not prose)
    keyword_code_token_types: ClassVar[set[str]] = {
        "IF",
        "INLINE IF",
        "ELSE IF",
        "ELSE",
        "END",
        "FOR",
        "FOR SEPARATOR",
        "WHILE",
        "TRY",
        "EXCEPT",
        "FINALLY",
        "BREAK",
        "CONTINUE",
        "RETURN STATEMENT",
        "GROUP",
        "VAR",
        "TAGS",
        "ARGUMENTS",
        "DOCUMENTATION",
        "SETUP",
        "TEARDOWN",
        "TEMPLATE",
        "TIMEOUT",
        "RETURN SETTING",
        "RETURN",
        "ASSIGN",
    }

    # Token types that indicate RF code in settings section context
    settings_code_token_types: ClassVar[set[str]] = {
        "LIBRARY",
        "RESOURCE",
        "VARIABLES",
        "DOCUMENTATION",
        "METADATA",
        "SUITE SETUP",
        "SUITE TEARDOWN",
        "TEST SETUP",
        "TEST TEARDOWN",
        "TEST TEMPLATE",
        "TEST TIMEOUT",
        "TEST TAGS",
        "TASK SETUP",
        "TASK TEARDOWN",
        "TASK TEMPLATE",
        "TASK TIMEOUT",
        "TASK TAGS",
        "KEYWORD TAGS",
        "FORCE TAGS",
        "DEFAULT TAGS",
    }

    # Control keywords that might appear as ERROR tokens when out of context
    control_keywords: ClassVar[set[str]] = {
        "ELSE",
        "ELSE IF",
        "END",
        "EXCEPT",
        "FINALLY",
        "BREAK",
        "CONTINUE",
        "RETURN",
    }

    # Setting pattern for ERROR tokens (settings valid only in specific contexts)
    setting_pattern = re.compile(
        r"^\[(Arguments|Tags|Documentation|Setup|Teardown|Template|Timeout|Return)\]$",
        re.IGNORECASE,
    )

    def visit_Comment(self, node: Comment) -> None:  # noqa: N802
        self.find_comments(node)

    def visit_CommentSection(self, _node: CommentSection) -> None:  # noqa: N802
        """Skip *** Comments *** section - it's meant for free-form text, not code."""

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.check_invalid_comments(node.name, node)
        self.generic_visit(node)

    visit_Keyword = visit_TestCase  # noqa: N815

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        self.find_comments(node, skip_commented_code=self.is_documentation_node(node))

    @staticmethod
    def is_documentation_node(node: Statement) -> bool:
        """
        Check if node is a Documentation statement where code examples are expected.

        Returns:
            True if node is a Documentation statement, False otherwise.

        """
        return isinstance(node, Documentation)

    def find_comments(self, node: Comment | Keyword | TestCase, skip_commented_code: bool = False) -> None:
        """
        Find comments in node and check them for validity.

        Line can have only one comment, but the comment can contain separators.
        If the comment have separator it will be recognized as COMMENT, SEPARATOR, COMMENT in AST.
        We need to merge such comments into one for validity checks.
        """
        for line in node.lines:
            first_comment = None
            merged_comment = ""
            prev_sep = ""
            for token in line:
                if token.type == Token.SEPARATOR:
                    prev_sep = token.value
                elif token.type == Token.COMMENT:
                    if first_comment:
                        merged_comment += prev_sep + token.value
                    else:
                        merged_comment = token.value
                        first_comment = token
            if first_comment:
                self.check_comment_content(first_comment, merged_comment, skip_commented_code)

    def check_invalid_comments(self, name: str, node: TestCase) -> None:
        if ROBOT_VERSION.major != 3:
            return
        if name and name.lstrip().startswith("#"):
            hash_pos = name.find("#")
            self.report(
                self.invalid_comment,
                node=node,
                col=node.col_offset + hash_pos + 1,
                end_col=len(name),
            )

    def check_comment_content(self, token: Token, content: str, skip_commented_code: bool = False) -> None:
        low_content = content.lower()
        for violation in [marker for marker in self.todo_in_comment.markers if marker in low_content]:
            index = low_content.find(violation)
            self.report(
                self.todo_in_comment,
                marker=content[index : index + len(violation)],
                lineno=token.lineno,
                col=token.col_offset + 1 + index,
                end_col=token.col_offset + 1 + index + len(violation),
            )
        if content.startswith("#") and not self.is_block_comment(content) and not content.startswith("# "):
            self.report(
                self.missing_space_after_comment,
                lineno=token.lineno,
                col=token.col_offset + 1,
            )
        if not skip_commented_code:
            self.check_for_commented_code(token, content)

    def check_for_commented_code(self, token: Token, content: str) -> None:
        """
        Check if comment contains Robot Framework code patterns using RF tokenizer.

        Args:
            token: The comment token being checked.
            content: The comment content including the '#' character.

        """
        # Strip leading # characters and whitespace to get comment body
        comment_body = content.lstrip("#").strip()
        if not comment_body:
            return

        # Skip if comment starts with ignore markers (TODO, FIXME, etc.)
        low_body = comment_body.lower()
        if any(low_body.startswith(marker) for marker in self.commented_out_code.markers):
            return

        # Check for RF code patterns using the tokenizer
        if self._is_rf_code(comment_body):
            # Extract a snippet for the message (first ~80 chars)
            snippet = comment_body[:80] + ("..." if len(comment_body) > 80 else "")
            self.report(
                self.commented_out_code,
                snippet=snippet,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + 1 + len(content),
            )

    def _is_rf_code(self, text: str) -> bool:
        """
        Check if text looks like RF code using Robot Framework's tokenizer.

        Args:
            text: Text to check for RF code patterns.

        Returns:
            True if text contains RF code patterns, False otherwise.

        """
        # Try settings context first for Library, Resource, Variables, etc.
        # These are more definitive indicators of commented-out code
        # Then try keyword context for control structures, assignments, etc.
        return self._is_rf_code_in_settings_context(text) or self._is_rf_code_in_keyword_context(text)

    def _is_rf_code_in_settings_context(self, text: str) -> bool:
        """
        Check if text looks like RF code in a settings section context.

        Args:
            text: Text to check for RF code patterns.

        Returns:
            True if text contains RF code patterns in settings context, False otherwise.

        """
        robot_code = f"*** Settings ***\n{text}\n"
        line_tokens = get_line_tokens(robot_code, lineno=2)
        if not line_tokens:
            return False
        token_types = {t.type for t in line_tokens}
        return bool(token_types & self.settings_code_token_types)

    def _is_rf_code_in_keyword_context(self, text: str) -> bool:
        """
        Check if text looks like RF code in a keyword context.

        Args:
            text: Text to check for RF code patterns.

        Returns:
            True if text contains RF code patterns in keyword context, False otherwise.

        """
        robot_code = f"*** Keywords ***\nKeyword\n    {text}\n"
        line_tokens = get_line_tokens(robot_code, lineno=3)
        if not line_tokens:
            return False

        token_types = {t.type for t in line_tokens}

        # Direct match with code token types
        if token_types & self.keyword_code_token_types:
            return True

        # Check ERROR tokens - might be control keywords or settings out of context
        first_token = line_tokens[0]
        if first_token.type == "ERROR":
            value = first_token.value
            # Check if it's an uppercase control keyword
            if value in self.control_keywords:
                return True
            # Check if it's a setting bracket
            if self.setting_pattern.match(value):
                return True

        # Check KEYWORD tokens - in older RF versions (4.x, 5.x), standalone control keywords
        # like ELSE, END, etc. are tokenized as KEYWORD instead of ERROR
        return bool(first_token.type == "KEYWORD" and first_token.value in self.control_keywords)

    def is_block_comment(self, comment: str) -> bool:
        return comment == "#" or self.missing_space_after_comment.block.match(comment) is not None
