"""Comments checkers"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from robot.api import Token, get_tokens

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit, TextEditKind
from robocop.linter.rules import (
    FixableRule,
    Rule,
    RuleParam,
    RuleSeverity,
)

if TYPE_CHECKING:
    from robocop.linter.diagnostics import Diagnostic


def regex(value: str) -> re.Pattern[str]:
    try:
        return re.compile(value)
    except re.error as regex_err:
        raise ValueError(f"Regex error: {regex_err}") from None


def lower_csv(value: str) -> list[str]:
    return value.lower().split(",")


def get_line_tokens(robot_code: str, lineno: int) -> list[Token] | None:
    """
    Tokenize RF code and return tokens from the specified line, excluding structural tokens.

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


class MissingSpaceAfterCommentRule(FixableRule):
    """
    No space after the ``#`` character and comment body.

    Comments usually start from the new line, or after 2 spaces in the same line. '#' characters denote the start of the
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

    The fix adds the missing space. Comments that would still violate the rule after adding the space
    (such as ``##comment``, which is not recognized as a block comment) are not fixed.

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
    fix_availability = FixAvailability.SOMETIMES

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """
        Add a missing space between the leading ``#`` characters and the comment body.

        Comments that would still violate the rule after adding the space (such as ``##comment``, which is not
        recognized as a block comment) are not fixed.
        """
        lineno, col = diag.range.start.line, diag.range.start.character
        comment = source_lines[lineno - 1][col - 1 :].rstrip("\n")
        hashes = len(comment) - len(comment.lstrip("#"))
        if not hashes:
            return None
        fixed_comment = f"{'#' * hashes} {comment[hashes:]}"
        if hashes > 1 and not self.block.match(fixed_comment):
            return None
        column = col + hashes
        return Fix(
            edits=[
                TextEdit(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    start_line=lineno,
                    start_col=column,
                    end_line=lineno,
                    end_col=column,
                    replacement=" ",
                    kind=TextEditKind.REPLACEMENT,
                )
            ],
            message="Add missing space after the comment character",
            applicability=FixApplicability.SAFE,
        )


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


class IgnoredDataRule(FixableRule):
    """
    Ignored data found in the file.

    All lines before the first test data section ([ref](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#test-data-sections))
    are ignored. It's recommended to add a `` *** Comments *** `` section header for lines that should be ignored.

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

    The fix adds the ``*** Comments ***`` section header before the ignored data. Data containing the language
    header is not fixed, since the header would stop working inside the ``*** Comments ***`` section.

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
    fix_availability = FixAvailability.SOMETIMES

    SECTION_HEADER = "***"
    IGNORE_DIRECTIVES = ("# robocop:", "# fmt:")
    LANGUAGE_HEADER = "language:"

    def check(self, lines: list[str], is_bom: bool) -> None:
        """Scan lines preceding the first section header and report them as ignored data."""
        if not self.enabled:
            return
        # ignore empty lines if the language header or robocop disabler is present
        ignore_empty_lines = False
        for lineno, line in enumerate(lines, start=1):
            if line.startswith(self.SECTION_HEADER):
                return
            if line.startswith(self.IGNORE_DIRECTIVES):
                ignore_empty_lines = True
                continue
            if lineno == 1:
                if line.lower().startswith(self.LANGUAGE_HEADER):
                    ignore_empty_lines = True
                    continue
                if is_bom:
                    # if it's BOM encoded file, the first line can be ignored
                    if "***" in line:
                        return
                    continue
            if ignore_empty_lines and not line.strip():
                continue
            self.report(lineno=lineno, col=1, end_col=len(line.rstrip()) + 1)
            return

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """
        Add the ``*** Comments ***`` section header before the ignored data.

        The header is not added if the ignored data contains the language header - it would be placed inside the
        ``*** Comments ***`` section and stop working.
        """
        for line in source_lines[diag.range.start.line - 1 :]:
            stripped = line.strip()
            if stripped.startswith(self.SECTION_HEADER):
                break
            if stripped.lower().startswith(self.LANGUAGE_HEADER):
                return None
        return Fix(
            edits=[TextEdit.insert_at_range(self.rule_id, self.name, diag.range, "*** Comments ***\n")],
            message="Add the '*** Comments ***' section header before the ignored data",
            applicability=FixApplicability.SAFE,
        )


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

    def check(self, is_bom: bool) -> None:
        if not self.enabled or not is_bom:
            return
        self.report(lineno=1, col=1)


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
