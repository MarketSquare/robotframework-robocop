"""Comments checkers"""

from __future__ import annotations

import re
from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE
from typing import TYPE_CHECKING, ClassVar

from robot.api import Token, get_tokens
from robot.parsing.model.statements import Documentation

from robocop.linter import sonar_qube
from robocop.linter.rules import (
    RawFileChecker,
    Rule,
    RuleParam,
    RuleSeverity,
    VisitorChecker,
)
from robocop.version_handling import ROBOT_VERSION

if TYPE_CHECKING:
    from pathlib import Path

    from robot.parsing.model import Keyword, Statement, TestCase
    from robot.parsing.model.blocks import CommentSection
    from robot.parsing.model.statements import Comment


def regex(value: str) -> re.Pattern:
    try:
        return re.compile(value)
    except re.error as regex_err:
        raise ValueError(f"Regex error: {regex_err}") from None


def lower_csv(value: str) -> list[str]:
    return value.lower().split(",")


def get_line_tokens(robot_code: str, lineno: int) -> list[Token] | None:
    """
    Tokenize RF code and return tokens from specified line, excluding structural tokens.

    Args:
        robot_code: Robot Framework code to tokenize.
        lineno: Line number to extract tokens from.

    Returns:
        List of tokens from the specified line, or None if tokenization fails.

    """
    try:
        tokens = list(get_tokens(robot_code, data_only=False))
        return [t for t in tokens if t.lineno == lineno and t.type not in {"EOL", "EOS", "SEPARATOR"}]
    except (TypeError, ValueError, AttributeError):
        return None


class ToDoInCommentRule(Rule):
    """
    TODO-like marker found in the comment.

    By default, it reports ``TODO`` and ``FIXME`` markers.

    Example:
        # TODO: Refactor this code
        # fixme

    Configuration example:

        robocop check --configure "todo-in-comment.markers=todo,Remove me,Fix this!"

    """

    name = "todo-in-comment"
    rule_id = "COM01"
    message = "Found a marker '{marker}' in the comments"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    parameters = [
        RuleParam(
            name="markers",
            default="todo,fixme",
            converter=lower_csv,
            show_type="comma separated value",
            desc="List of case-insensitive markers that violate the rule in comments.",
        )
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0701",)


class MissingSpaceAfterCommentRule(Rule):
    """
    No space after the ``#`` character and comment body.

    Comments usually starts from the new line, or after 2 spaces in the same line. '#' characters denotes start of the
    comment, followed by the space and comment body:

        # stand-alone comment
        Keyword Call  # inline comment
        ### block comments are fine ###

    Deviating from this pattern may lead to inconsistent or less readable comment format.

    It is possible to configure block comments syntax that should be ignored.
    Configured regex for block comment should take into account the first character is ``#``.

    Example:
        #bad
        # good
        ### good block

    Configuration example:

        robocop check --configure missing-space-after-comment.block=^#[*]+

    Allows commenting like:

        #*****
        #
        # Important topics here!
        #
        #*****
        or
        #* Headers *#

    """

    name = "missing-space-after-comment"
    rule_id = "COM02"
    message = "Missing blank space after comment character"
    severity = RuleSeverity.INFO  # TODO: changed severity from warning to info
    added_in_version = "1.0.0"
    parameters = [
        RuleParam(
            name="block",
            default="^###",
            converter=regex,
            desc="Block comment regex pattern.",
        )
    ]
    style_guide_ref = ["#comments"]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0702",)


class InvalidCommentRule(Rule):
    """
    Invalid comment.

    In Robot Framework 3.2.2, comments that started from the second character in the line were not recognised as
    comments. '#' characters need to be in first or any other than the second character in the line to be recognised
    as a comment.

    Example:
    ```text
    # good
     # bad
      # third cell so it's good
    ```

    """

    name = "invalid-comment"
    rule_id = "COM03"
    message = "Comment starts from the second character in the line"
    severity = RuleSeverity.ERROR
    version = "<4.0"
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE,
        issue_type=sonar_qube.SonarQubeIssueType.BUG,
    )
    deprecated_names = ("0703",)
    # TODO: deprecate (<4)


class IgnoredDataRule(Rule):
    """
    Ignored data found in file.

    All lines before first test data section
    (`ref <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-data-sections>`_)
    are ignored. It's recommended to add ``*** Comments ***`` section header for lines that should be ignored.

    Missing section header:

        Resource   file.resource  # it looks like *** Settings *** but section header is missing - line is ignored

        *** Keywords ***
        Keyword Name
           No Operation

    Comment lines that should be inside ``*** Comments ***``:

        Deprecated Test
            Keyword
            Keyword 2

        *** Test Cases ***

    """

    name = "ignored-data"
    rule_id = "COM04"
    message = "Ignored data found in file"
    severity = RuleSeverity.WARNING
    added_in_version = "1.3.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0704",)


class BomEncodingRule(Rule):
    """
    BOM (Byte Order Mark) found in the file.

    Some code editors can save Robot file using BOM encoding.
    It is not supported by older versions of the Robot Framework.
    Ensure that the file is saved in UTF-8 encoding.

    Changes in 8.0.0: Rule is now optional since Robot Framework now supports BOM encoding.

    """

    name = "bom-encoding-in-file"
    rule_id = "COM05"
    message = "BOM (Byte Order Mark) found in the file"
    file_wide_rule = True
    severity = RuleSeverity.WARNING
    added_in_version = "1.7.0"
    enabled = False
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0705",)


class CommentedOutCodeRule(Rule):
    """
    Commented out code detected.

    Uses Robot Framework's tokenizer to detect comments that contain RF code syntax.
    This approach reliably identifies:

    - **Variable assignment**: ``${var}=``, ``@{list}=``, ``&{dict}=``
    - **Setting brackets**: ``[Tags]``, ``[Arguments]``, ``[Documentation]``, ``[Setup]``,
      ``[Teardown]``, ``[Template]``, ``[Timeout]``, ``[Return]``
    - **Control structures**: ``IF``, ``ELSE``, ``ELSE IF``, ``END``, ``FOR``,
      ``WHILE``, ``TRY``, ``EXCEPT``, ``FINALLY``, ``BREAK``, ``CONTINUE``, ``RETURN``,
      ``GROUP``, ``VAR``
    - **Settings section statements**: ``Library``, ``Resource``, ``Variables``,
      ``Suite Setup``, ``Suite Teardown``, ``Test Setup``, ``Test Teardown``,
      ``Metadata``, ``Force Tags``, ``Default Tags``

    The following are ignored:

    - Comments starting with TODO/FIXME markers (configurable)
    - Comments inside ``[Documentation]`` sections (code examples are common there)
    - Plain prose comments (e.g., "If you need help" is not detected as IF statement)

    This rule is disabled by default. Enable it to detect forgotten or accidentally
    commented-out code.

    Example of violations:

        Keyword
            # ${result}=    Get Value
            # [Tags]    smoke
            # IF    ${condition}
            Other Keyword

    Example of valid comments:

        # This is a normal comment
        # TODO: implement this feature
        # If you need help, ask

    """

    name = "commented-out-code"
    rule_id = "COM06"
    message = "Commented out code: '{snippet}'"
    severity = RuleSeverity.WARNING
    added_in_version = "7.1.0"
    enabled = False
    parameters = [
        RuleParam(
            name="markers",
            default="todo,fixme",
            converter=lower_csv,
            show_type="comma separated value",
            desc="Markers that indicate legitimate comments (not code). "
            "Comments starting with these markers are ignored.",
        )
    ]
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )


class CommentChecker(VisitorChecker):
    """Checker for comments content. It detects invalid comments or leftovers like `todo` or `fixme` in the code."""

    todo_in_comment: ToDoInCommentRule
    missing_space_after_comment: MissingSpaceAfterCommentRule
    invalid_comment: InvalidCommentRule
    commented_out_code: CommentedOutCodeRule

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


class IgnoredDataChecker(RawFileChecker):
    """Checker for ignored data."""

    ignored_data: IgnoredDataRule
    bom_encoding_in_file: BomEncodingRule

    BOM = [BOM_UTF32_BE, BOM_UTF32_LE, BOM_UTF8, BOM_UTF16_LE, BOM_UTF16_BE]
    SECTION_HEADER = "***"
    IGNORE_DIRECTIVES = ("# robocop:", "# fmt:")
    LANGUAGE_HEADER = "language:"

    def __init__(self) -> None:
        self.is_bom = False
        self.ignore_empty_lines = False  # ignore empty lines if the language header or robocop disabler is present
        super().__init__()

    def parse_file(self) -> None:
        self.is_bom = False
        self.ignore_empty_lines = False
        self.detect_bom(self.source_file.path)
        if not self.ignored_data.enabled:
            return
        for lineno, line in enumerate(self.source_file.source_lines, start=1):
            if self.check_line(line, lineno):
                break

    def check_line(self, line: str, lineno: int) -> bool:
        if line.startswith(self.SECTION_HEADER):
            return True
        if line.startswith(self.IGNORE_DIRECTIVES):
            self.ignore_empty_lines = True
            return False
        if lineno == 1:
            if line.lower().startswith(self.LANGUAGE_HEADER):
                self.ignore_empty_lines = True
                return False
            if self.is_bom:
                # if it's BOM encoded file, first line can be ignored
                return "***" in line
        if self.ignore_empty_lines and not line.strip():
            return False
        self.report(self.ignored_data, lineno=lineno, col=1, end_col=len(line.rstrip()) + 1)
        return True

    def detect_bom(self, source: Path):
        with open(source, "rb") as raw_file:
            first_four = raw_file.read(4)
            self.is_bom = any(first_four.startswith(bom_marker) for bom_marker in IgnoredDataChecker.BOM)
            if self.is_bom:
                self.report(self.bom_encoding_in_file, lineno=1, col=1)
