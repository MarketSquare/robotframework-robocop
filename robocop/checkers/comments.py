"""
Comments checkers
"""
import re

from codecs import BOM_UTF8, BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE

from robot.api import Token
from robot.utils import FileReader

from robocop.checkers import RawFileChecker, VisitorChecker
from robocop.rules import Rule, RuleSeverity, RuleParam
from robocop.utils import ROBOT_VERSION
from robocop.exceptions import ConfigGeneralError

def regex(value):
    converted = rf'{value}'
    try:
        return re.compile(converted)
    except re.error as regex_err:
        raise ValueError(f'Regex error: {regex_err}')

rules = {
    "0701": Rule(
        RuleParam(
            name="markers",
            default="todo,fixme",
            converter=str,
            desc="List of case-insensitive markers that violate the rule in comments.",
        ),
        rule_id="0701",
        name="todo-in-comment",
        msg="Found a marker '{{ marker }}' in the comments",
        severity=RuleSeverity.WARNING,
        docs="""
        Report occurrences of the configured, case-insensitive marker in the comments.
        By default, it reports TODO and FIXME markers.

        Example::
        
            # TODO: Refactor this code
            # fixme
        
        Configuration example::

            robocop --configure "todo-in-comment:markers:todo,Remove me,Fix this!"

        """,
    ),
    "0702": Rule(
        RuleParam(
            name="block",
            default="^###",
            converter=regex,
            desc="Block comment regex pattern.",
        ),
        rule_id="0702",
        name="missing-space-after-comment",
        msg="Missing blank space after comment character",
        severity=RuleSeverity.WARNING,
        docs="""
        Make sure to have one blank space after '#' comment character.
        Configured regex for block comment should take into account the first character is `#`.

        Example::
        
            #bad
            # good
            ### good block

        Configuration example::

            robocop --configure missing-space-after-comment:block:^#[*]+

            Allows commenting like:

                #*****
                #
                # Important topics here!
                #
                #*****
                or
                #* Headers *#

        """,
    ),
    "0703": Rule(
        rule_id="0703",
        name="invalid-comment",
        msg="Invalid comment. '#' needs to be first character in the cell. "
        "For block comments you can use '*** Comments ***' section",
        severity=RuleSeverity.ERROR,
        version="<4.0",
        docs="""
        In Robot Framework 3.2.2 comments that started from second character in the cell were not recognized as 
        comments.
        
        Example::
        
            # good
             # bad
              # third cell so it's good
        
        """,
    ),
    "0704": Rule(
        rule_id="0704",
        name="ignored-data",
        msg="Ignored data found in file",
        severity=RuleSeverity.WARNING,
        docs="""
        All lines before first test data section 
        (`ref <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-data-sections>`_) 
        are ignored. It's recommended to add `*** Comments ***` section header for lines that should be ignored.
        
        Missing section header::
    
            Resource   file.resource  # it looks like *** Settings *** but section header is missing - line is ignored
            
            *** Keywords ***
            Keyword Name
               No Operation
        
        Comment lines that should be inside `*** Comments ***`::
            
            Deprecated Test
                Keyword
                Keyword 2
            
            *** Test Cases ***
    
        """,
    ),
    "0705": Rule(
        rule_id="0705",
        name="bom-encoding-in-file",
        msg="This file contains BOM (Byte Order Mark) encoding not supported by Robot Framework",
        severity=RuleSeverity.WARNING,
        docs="""
        Some code editors can save Robot file using BOM encoding. Ensure that file is saved in UTF-8 encoding.
        """,
    ),
}


class CommentChecker(VisitorChecker):
    """Checker for comments content. It detects invalid comments or leftovers like `todo` or `fixme` in the code."""

    reports = (
        "todo-in-comment",
        "missing-space-after-comment",
        "invalid-comment",
    )

    def __init__(self):
        self._markers = None
        self._block = None
        super().__init__()

    @property
    def markers(self):
        if not self._markers:
            self._markers = self.param("todo-in-comment", "markers").lower().split(",")
        return self._markers

    @property
    def block(self):
        if not self._block:
            self._block = self.param("missing-space-after-comment", "block")
        return self._block

    def visit_Comment(self, node):  # noqa
        self.find_comments(node)

    def visit_TestCase(self, node):  # noqa
        self.check_invalid_comments(node.name, node)
        self.generic_visit(node)

    visit_Keyword = visit_TestCase

    def visit_Statement(self, node):  # noqa
        self.find_comments(node)

    def find_comments(self, node):
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

    def check_invalid_comments(self, name, node):
        if ROBOT_VERSION.major != 3:
            return
        if name and name.lstrip().startswith("#"):
            hash_pos = name.find("#")
            self.report("invalid-comment", node=node, col=node.col_offset + hash_pos + 1)

    def check_comment_content(self, token, content):
        low_content = content.lower()
        for violation in [marker for marker in self.markers if marker in low_content]:
            index = low_content.find(violation)
            self.report(
                "todo-in-comment",
                marker=content[index:index+len(violation)],
                lineno=token.lineno,
                col=token.col_offset + 1 + index,
            )
        if content.startswith("#") and not self.is_block_comment(content):
            if not content.startswith("# "):
                self.report(
                    "missing-space-after-comment",
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                )

    def is_block_comment(self, comment):
        return comment == "#" or self.block.match(comment) is not None


class IgnoredDataChecker(RawFileChecker):
    """Checker for ignored data."""

    reports = (
        "ignored-data",
        "bom-encoding-in-file",
    )
    BOM = [BOM_UTF32_BE, BOM_UTF32_LE, BOM_UTF8, BOM_UTF16_LE, BOM_UTF16_BE]

    def __init__(self):
        self.is_bom = False
        super().__init__()

    def parse_file(self):
        self.is_bom = False
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

    def check_line(self, line, lineno):
        if line.startswith("***"):
            return True
        if not line.startswith("# robocop:"):
            if lineno == 1 and self.is_bom:
                # if it's BOM encoded file, first line can be ignored
                return "***" in line
            self.report("ignored-data", lineno=lineno, col=1)
            return True
        return False

    def detect_bom(self, source):
        with open(source, "rb") as raw_file:
            first_four = raw_file.read(4)
            self.is_bom = any(first_four.startswith(bom_marker) for bom_marker in IgnoredDataChecker.BOM)
            if self.is_bom:
                self.report("bom-encoding-in-file", lineno=1, col=1)
