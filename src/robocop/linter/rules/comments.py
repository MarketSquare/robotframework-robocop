"""Comments checkers"""

from __future__ import annotations

import re
from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE
from typing import TYPE_CHECKING

from robot.api import Token
from robot.utils import FileReader

from robocop.linter.rules import RawFileChecker, Rule, RuleParam, RuleSeverity, VisitorChecker
from robocop.linter.utils import ROBOT_VERSION

if TYPE_CHECKING:
    from robot.parsing.model import Keyword, Statement, TestCase
    from robot.parsing.model.statements import Comment


def regex(value: str) -> re.Pattern:
    try:
        return re.compile(value)
    except re.error as regex_err:
        raise ValueError(f"Regex error: {regex_err}") from None


def lower_csv(value: str) -> list[str]:
    return value.lower().split(",")


class ToDoInCommentRule(Rule):
    """
    TODO-like marker found in the comment.

    By default, it reports ``TODO`` and ``FIXME`` markers.

    Example::

        # TODO: Refactor this code
        # fixme

    Configuration example::

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


class MissingSpaceAfterCommentRule(Rule):
    """
    No space after the ``#`` character and comment body.

    Comments usually starts from the new line, or after 2 spaces in the same line. '#' characters denotes start of the
    comment, followed by the space and comment body::

        # stand-alone comment
        Keyword Call  # inline comment
        ### block comments are fine ###

    Deviating from this pattern may lead to inconsistent or less readable comment format.

    It is possible to configure block comments syntax that should be ignored.
    Configured regex for block comment should take into account the first character is ``#``.

    Example::

        #bad
        # good
        ### good block

    Configuration example::

        robocop check --configure missing-space-after-comment.block=^#[*]+

    Allows commenting like::

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
    parameters = [RuleParam(name="block", default="^###", converter=regex, desc="Block comment regex pattern.")]
    style_guide_ref = ["#comments"]


class InvalidCommentRule(Rule):
    """
    Invalid comment.

    In Robot Framework 3.2.2 comments that started from second character in the line were not recognized as
    comments. '#' characters needs to be in first or any other than second character in the line to be recognized
    as a comment.

    Example::

        # good
         # bad
          # third cell so it's good

    """

    name = "invalid-comment"
    rule_id = "COM03"
    message = "Comment starts from the second character in the line"
    severity = RuleSeverity.ERROR
    version = "<4.0"
    added_in_version = "1.0.0"


class IgnoredDataRule(Rule):
    """
    Ignored data found in file.

    All lines before first test data section
    (`ref <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-data-sections>`_)
    are ignored. It's recommended to add ``*** Comments ***`` section header for lines that should be ignored.

    Missing section header::

        Resource   file.resource  # it looks like *** Settings *** but section header is missing - line is ignored

        *** Keywords ***
        Keyword Name
           No Operation

    Comment lines that should be inside ``*** Comments ***``::

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


class BomEncodingRule(Rule):
    """
    BOM (Byte Order Mark) found in the file.

    Some code editors can save Robot file using BOM encoding. It is not supported by the Robot Framework.
    Ensure that file is saved in UTF-8 encoding.

    """

    name = "bom-encoding-in-file"
    rule_id = "COM05"
    message = "BOM (Byte Order Mark) found in the file"
    file_wide_rule = True
    severity = RuleSeverity.WARNING
    added_in_version = "1.7.0"


class CommentChecker(VisitorChecker):
    """Checker for comments content. It detects invalid comments or leftovers like `todo` or `fixme` in the code."""

    todo_in_comment: ToDoInCommentRule
    missing_space_after_comment: MissingSpaceAfterCommentRule
    invalid_comment: InvalidCommentRule

    def visit_Comment(self, node: Comment) -> None:  # noqa: N802
        self.find_comments(node)

    def visit_TestCase(self, node: TestCase) -> None:  # noqa: N802
        self.check_invalid_comments(node.name, node)
        self.generic_visit(node)

    visit_Keyword = visit_TestCase  # noqa: N815

    def visit_Statement(self, node: Statement) -> None:  # noqa: N802
        self.find_comments(node)

    def find_comments(self, node: Comment | Keyword | TestCase) -> None:
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
                self.check_comment_content(first_comment, merged_comment)

    def check_invalid_comments(self, name: str, node: TestCase) -> None:
        if ROBOT_VERSION.major != 3:
            return
        if name and name.lstrip().startswith("#"):
            hash_pos = name.find("#")
            self.report(self.invalid_comment, node=node, col=node.col_offset + hash_pos + 1, end_col=len(name))

    def check_comment_content(self, token: Token, content: str) -> None:
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

    def __init__(self):
        self.is_bom = False
        self.ignore_empty_lines = False  # ignore empty lines if language header or robocop disabler is present
        super().__init__()

    def parse_file(self) -> None:
        self.is_bom = False
        self.ignore_empty_lines = False
        if self.lines is not None:
            for lineno, line in enumerate(self.lines, start=1):
                if self.check_line(line, lineno):
                    break
        else:
            self.detect_bom(self.source)
            with FileReader(self.source) as file_reader:
                for lineno, line in enumerate(file_reader.readlines(), start=1):
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
        self.report(self.ignored_data, lineno=lineno, col=1, end_col=len(line))
        return True

    def detect_bom(self, source: str):
        with open(source, "rb") as raw_file:
            first_four = raw_file.read(4)
            self.is_bom = any(first_four.startswith(bom_marker) for bom_marker in IgnoredDataChecker.BOM)
            if self.is_bom:
                self.report(self.bom_encoding_in_file, lineno=1, col=1)
