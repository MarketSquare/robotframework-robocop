"""Miscellaneous checkers"""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from robot.api import Token
from robot.parsing.model.blocks import TestCaseSection
from robot.parsing.model.statements import KeywordCall, Teardown
from robot.variables.search import search_variable

# TODO: Validate which ImportError we can drop now (with 5+)
try:
    from robot.api.parsing import Comment, EmptyLine, Variable
except ImportError:
    from robot.parsing.model.statements import Comment, EmptyLine, Variable
try:
    from robot.api.parsing import Break, Continue, InlineIfHeader
except ImportError:
    InlineIfHeader, Break, Continue = None, None, None
try:  # RF 7+
    from robot.api.parsing import Var
except ImportError:
    Var = None

from robocop.formatter.utils.inline_if import InlineIfConverter
from robocop.linter import sonar_qube
from robocop.linter.fix import (
    Fix,
    FixApplicability,
    FixAvailability,
    TextEdit,
    remove_lines_fix,
    remove_statement_fix,
)
from robocop.linter.rules import (
    FixableRule,
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
)
from robocop.linter.utils import misc as utils
from robocop.source_file import StatementLinesCollector

if TYPE_CHECKING:
    from robot.parsing.model import File
    from robot.parsing.model.blocks import Block, If, VariableSection
    from robot.parsing.model.statements import Error, Node

    from robocop.linter.diagnostics import Diagnostic


FOR_LOOP_KEYWORDS = frozenset(
    {
        "continueforloop",
        "continueforloopif",
        "exitforloop",
        "exitforloopif",
    }
)
COMPARISON_SIGNS = frozenset({"==", "!="})
EMPTY_COMPARISON = frozenset({"${true}", "${false}", "true", "false", "[]", "{}", "set()", "list()", "dict()"})
NEGATIVE_CONDITION_PARTS = 4  # not ${variable} is None
# Two character operators need to be listed before the single character ones sharing a prefix (e.g. '>=' before '>').
COMPARISON_OPERATORS = ("==", "!=", ">=", "<=", ">", "<")


def tokens_length(tokens: list[Token]) -> int:
    return sum(len(token.value) for token in tokens)


def normalize_var_name(name: str) -> str:
    return name.lower().replace("_", "").replace(" ", "").replace("=", "")


def assign_tokens_are_equal(if_node: Node, other_if_node: Node) -> bool:
    assign_1 = getattr(if_node, "assign", None)
    assign_2 = getattr(other_if_node, "assign", None)
    if assign_1 is None or assign_2 is None:
        return all(assign is None for assign in (assign_1, assign_2))
    if len(assign_1) != len(assign_2):
        return False
    return all(
        normalize_var_name(var1) == normalize_var_name(var2) for var1, var2 in zip(assign_1, assign_2, strict=False)
    )


def conditions_are_equal(if_node: Node, other_if_node: Node) -> bool:
    """Check whether two IF blocks have the same conditions in every branch and assign to the same variables."""
    if not assign_tokens_are_equal(if_node, other_if_node):
        return False
    while if_node is not None and other_if_node is not None:
        if if_node.condition != other_if_node.condition:
            return False
        if_node = if_node.orelse
        other_if_node = other_if_node.orelse
    return if_node is None and other_if_node is None


class KeywordAfterReturnRule(Rule):
    """
    Keyword call after the `` [Return]`` setting.

    To improve readability, use ``[Return]`` setting at the end of the keyword. If you want to return immediately
    from the keyword, use the ``RETURN`` statement instead. ``[Return]`` does not return from the keyword but only
    sets the values that will be returned at the end of the keyword.

    Incorrect code example:

        *** Keywords ***
        Keyword
            Step
            [Return]    ${variable}
            ${variable}    Other Step

    Correct code:

        *** Keywords ***
        Keyword
            Step
            ${variable}    Other Step
            [Return]    ${variable}

    """

    name = "keyword-after-return"
    rule_id = "MISC01"
    message = "{error_msg}"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0901",)

    def check(self, node: Block) -> None:
        """Report a keyword call placed after the keyword already returned."""
        if not self.enabled:
            return
        return_node: Node | None = None
        keyword_after_return = False
        return_from = False
        error = ""
        for child in node.body:
            if isinstance(child, utils.RETURN_CLASSES.return_setting_class):
                return_node = child
                error = (
                    "[Return] is not defined at the end of keyword. "
                    "Note that [Return] does not quit from keyword but only set variables to be returned"
                )
            elif not isinstance(child, (EmptyLine, Comment, Teardown)) and return_node is not None:
                keyword_after_return = True
            if isinstance(child, KeywordCall):
                if return_from:
                    keyword_after_return = True
                    return_node = child
                    error = "Keyword call after 'Return From Keyword'"
                elif utils.normalize_robot_name(child.keyword, remove_prefix="builtin.") == "returnfromkeyword":
                    return_from = True
        if keyword_after_return and return_node is not None:
            token = return_node.data_tokens[0]
            self.report(
                error_msg=error,
                node=token,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )


class EmptyReturnRule(FixableRule):
    """
    ``[Return]`` is empty.

    ``[Return]`` statement is used to define variables returned from keyword. If you don't return anything from
    a keyword, don't use ``[Return]``.

    Incorrect code example:

        *** Keywords ***
        Keyword
            Gather Results
            Assert Results
            [Return]

    Correct code:

        *** Keywords ***
        Keyword
            Gather Results
            Assert Results

    The fix removes the empty ``[Return]`` setting. Comments are not removed.

    """

    name = "empty-return"
    rule_id = "MISC02"
    message = "[Return] is empty"
    severity = RuleSeverity.WARNING
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0903",)
    fix_availability = FixAvailability.ALWAYS

    def check(self, node: Block) -> None:
        """Report ``[Return]`` settings that do not return any value."""
        if not self.enabled:
            return
        for child in node.body:
            if isinstance(child, utils.RETURN_CLASSES.return_setting_class) and not child.values:
                token = child.data_tokens[0]
                self.report(
                    node=child,
                    col=token.col_offset + 1,
                    end_col=token.col_offset + len(token.value),
                )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Remove the empty ``[Return]`` setting."""
        if diag.node is None:
            return None
        return remove_statement_fix(self, diag.node, source_lines, "Remove empty '[Return]' setting")


class NestedForLoopRule(Rule):
    """
    Not supported nested for loop.

    Older versions of Robot Framework did not support nested for loops:

        *** Test Cases
        Test case
            FOR    ${var}    IN RANGE    10
                FOR   ${other_var}   IN    a  b
                    # Nesting supported from Robot Framework 4.0+
                END
            END

    """

    name = "nested-for-loop"
    rule_id = "MISC03"
    message = "Not supported nested for loop"
    severity = RuleSeverity.ERROR
    version = "<4.0"
    added_in_version = "1.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0907",)

    def check(self, node: Node) -> None:
        """Report FOR loops nested directly in another FOR loop."""
        if not self.enabled:
            return
        for child in node.body:
            if child.type == "FOR":
                token = child.get_token(Token.FOR)
                self.report(
                    node=child,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )


class InconsistentAssignmentRule(FixableRule):
    """
    Not consistent assignment sign in the file.

    Use only one type of assignment sign in a file. Assignment signs are checked in the keyword calls and in the
    ``VAR`` syntax (Robot Framework 7 and newer). The ``*** Variables ***`` section is handled by the
    ``inconsistent-assignment-in-variables`` rule.

    Incorrect code example:

        *** Keywords ***
        Keyword
            ${var} =  Other Keyword
            No Operation

        Keyword 2
            No Operation
            ${var}  ${var2}    Some Keyword

    Correct code:

        *** Keywords ***
        Keyword
            ${var}    Other Keyword
            No Operation

        Keyword 2
            No Operation
            ${var}  ${var2}    Some Keyword

    By default, Robocop looks for the most popular assignment sign in the file. It is possible to define the expected
    assignment sign:

    === ":octicons-command-palette-24: cli"

    ```bash
    robocop check --configure inconsistent-assignment.assignment_sign_type=none
    ```

    === ":material-file-cog-outline: toml"

        ```toml
        [tool.robocop.lint]
        configure = [
            "inconsistent-assignment.assignment_sign_type=none"
        ]
        ```

    You can choose between the following assignment signs:

    - 'autodetect' (default),
    - 'none',
    - 'equal_sign' (``=``)
    - 'space_and_equal_sign' (`` =``).

    The assignment sign can be replaced with the expected one automatically with the ``--fix`` option.

    """

    name = "inconsistent-assignment"
    rule_id = "MISC04"
    message = (
        "The assignment sign is not consistent within the file. "
        "Expected '{expected_sign}' but got '{actual_sign}' instead"
    )
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=utils.parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
    ]
    added_in_version = "1.7.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0909",)

    def check(self, token: Token, expected_sign: str) -> None:
        if not self.enabled:
            return
        sign = utils.AssignmentTypeDetector.get_assignment_sign(token.value)
        if sign == expected_sign:
            return
        self.report(
            expected_sign=expected_sign,
            actual_sign=sign,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Replace the assignment sign with the expected one."""
        line = source_lines[diag.range.start.line - 1]
        variable = line[diag.range.start.character - 1 : diag.range.end.character - 1]
        actual_sign = str(diag.reported_arguments["actual_sign"])
        expected_sign = str(diag.reported_arguments["expected_sign"])
        if actual_sign and not variable.endswith(actual_sign):
            return None
        base = variable[: len(variable) - len(actual_sign)] if actual_sign else variable
        edit = TextEdit.replace_at_range(self.rule_id, self.name, diag.range, f"{base}{expected_sign}")
        return Fix(
            edits=[edit],
            message=f"Replace the '{actual_sign}' assignment sign with '{expected_sign}'",
            applicability=FixApplicability.SAFE,
        )


class InconsistentAssignmentInVariablesRule(FixableRule):
    """
    Not consistent assignment sign in the ``*** Variables ***`` section.

    Use one type of assignment sign in the Variables section.

    Incorrect code example:

        *** Variables ***
        ${var} =    1
        ${var2}=    2
        ${var3} =   3
        ${var4}     a
        ${var5}     b

    Correct code:

        *** Variables ***
        ${var}      1
        ${var2}     2
        ${var3}     3
        ${var4}     a
        ${var5}     b

    By default, Robocop looks for the most popular assignment sign in the file. It is possible to define the expected
    assignment sign by running:

        robocop check --configure inconsistent-assignment-in-variables.assignment_sign_type=equal_sign

    You can choose between the following signs:

    - 'autodetect' (default),
    - 'none',
    - 'equal_sign' (``=``)
    - 'space_and_equal_sign' (`` =``).

    The assignment sign can be replaced with the expected one automatically with the ``--fix`` option.

    """

    name = "inconsistent-assignment-in-variables"
    rule_id = "MISC05"
    message = (
        "The assignment sign is not consistent inside the variables section. "
        "Expected '{expected_sign}' but got '{actual_sign}' instead"
    )
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=utils.parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        )
    ]
    added_in_version = "1.7.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0910",)

    def check(self, node: VariableSection, expected_sign: str) -> None:
        if not self.enabled:
            return
        for child in node.body:
            if not isinstance(child, Variable) or child.errors:
                continue
            var_token = child.get_token(Token.VARIABLE)
            sign = utils.AssignmentTypeDetector.get_assignment_sign(var_token.value)
            if sign == expected_sign:
                continue
            self.report(
                expected_sign=expected_sign,
                actual_sign=sign,
                lineno=var_token.lineno,
                col=var_token.col_offset + 1,
                end_col=var_token.end_col_offset + 1,
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Replace the assignment sign with the expected one."""
        line = source_lines[diag.range.start.line - 1]
        variable = line[diag.range.start.character - 1 : diag.range.end.character - 1]
        actual_sign = str(diag.reported_arguments["actual_sign"])
        expected_sign = str(diag.reported_arguments["expected_sign"])
        if actual_sign and not variable.endswith(actual_sign):
            return None
        base = variable[: len(variable) - len(actual_sign)] if actual_sign else variable
        edit = TextEdit.replace_at_range(self.rule_id, self.name, diag.range, f"{base}{expected_sign}")
        return Fix(
            edits=[edit],
            message=f"Replace the '{actual_sign}' assignment sign with '{expected_sign}'",
            applicability=FixApplicability.SAFE,
        )


class CanBeResourceFileRule(Rule):
    """
    No tests in the file, consider renaming the file extension to ``.resource``.

    If the Robot file contains only keywords or variables, it's a good practice to use ``.resource`` extension.
    """

    name = "can-be-resource-file"
    rule_id = "MISC06"
    message = "No tests in '{file_name}' file, consider renaming to '{file_name_stem}.resource'"
    severity = RuleSeverity.INFO
    file_wide_rule = True
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0913",)

    def check(self, node: File, source: str) -> None:
        if not self.enabled or not source:
            return
        extension = Path(source).suffix
        file_name = Path(source).stem
        if (
            ".resource" not in extension
            and "__init__" not in file_name
            and node.sections
            and not any(isinstance(section, TestCaseSection) for section in node.sections)
        ):
            self.report(
                file_name=Path(source).name,
                file_name_stem=file_name,
                node=node,
            )


class IfCanBeMergedRule(Rule):
    """
    IF statement can be merged with the previous IF.

    ``IF`` statement follows another ``IF`` with identical conditions. It can be possibly merged into one.

    Example of rule violation:

        *** Test Cases ***
        Test case
            IF  ${var} == 4
                Keyword
            END
            # comments are ignored
            IF  ${var}  == 4
                Keyword 2
            END

    ``IF`` statement is considered identical only if all branches have identical conditions.

    Similar but not identical ``IF``:

        *** Test Cases ***
        Test case
            IF  ${variable}
                Keyword
            ELSE
                Other Keyword
            END
            IF  ${variable}
                Keyword
            END

    """

    name = "if-can-be-merged"
    rule_id = "MISC07"
    message = "IF statement can be merged with previous IF (defined in line {line})"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0914",)

    def check(self, node: If, previous_if: If) -> None:
        if not conditions_are_equal(node, previous_if):
            return
        token = node.header.get_token(node.header.type)
        self.report(
            line=previous_if.lineno,
            node=token,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )


class StatementOutsideLoopRule(Rule):
    """
    Loop statement used outside loop.

    Following keywords and statements should only be used inside loop (``WHILE`` or ``FOR``):
        - ``Exit For Loop``
        - ``Exit For Loop If``
        - ``Continue For Loop``
        - ``Continue For Loop If``
        - ``CONTINUE``
        - ``BREAK``

    """

    name = "statement-outside-loop"
    rule_id = "MISC08"
    message = "{name} {statement_type} used outside a loop"
    severity = RuleSeverity.ERROR
    version = ">=5.0"
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.BUG,
    )
    deprecated_names = ("0915",)

    def check_keyword(self, node: KeywordCall) -> None:
        """Check a keyword call that is only valid inside a FOR loop, such as ``Exit For Loop``."""
        if utils.normalize_robot_name(node.keyword, remove_prefix="builtin.") not in FOR_LOOP_KEYWORDS:
            return
        col = utils.keyword_col(node)
        self.report(
            name=f"'{node.keyword}'",
            statement_type="keyword",
            node=node,
            col=col,
            end_col=col + len(node.keyword),
        )

    def check_statement(self, node: Node, token_type: str) -> None:
        """Check a ``CONTINUE`` or ``BREAK`` statement used outside a loop."""
        if node.errors and f"{token_type} can only be used inside a loop." not in node.errors:
            return
        error_token = node.get_token(token_type)
        self.report(
            name=token_type,
            statement_type="statement",
            node=node,
            col=error_token.col_offset + 1,
            end_col=error_token.end_col_offset + 1,
        )

    def check_error(self, node: Error) -> None:
        """Check errors reported by Robot Framework itself. Supported since RF 6.1."""
        for error_token in node.get_tokens(Token.ERROR):
            if "is not allowed in this context" in error_token.error:
                self.report(
                    name=error_token.value,
                    statement_type="statement",
                    node=node,
                    col=error_token.col_offset + 1,
                    end_col=error_token.end_col_offset + 1,
                )


class InlineIfCanBeUsedRule(FixableRule):
    """
    IF can be replaced with inline IF.

    Short and simple ``IF`` statements can be replaced with ``inline IF``.

    Following ``IF``:

        IF    $condition
            BREAK
        END

    can be replaced with:

        IF    $condition    BREAK

    The fix replaces the ``IF`` block with an ``inline IF``.

    """

    name = "inline-if-can-be-used"
    rule_id = "MISC09"
    message = "IF can be replaced with inline IF"
    severity = RuleSeverity.INFO
    version = ">=5.0"
    parameters = [
        RuleParam(
            name="max_width",
            default=80,
            converter=int,
            desc="maximum width of IF (in characters) below which it will be recommended to use inline IF",
        ),
    ]
    severity_threshold = SeverityThreshold("max_width", compare_method="less")
    added_in_version = "2.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0916",)
    fix_availability = FixAvailability.SOMETIMES

    def check(self, node: If) -> None:
        if (
            len(node.body) != 1
            or node.orelse  # TODO: it could still report with orelse? if short enough
            # IF with one branch and assign require ELSE to be valid, better to ignore it
            or getattr(node.body[0], "assign", None)
            or not isinstance(node.body[0], (KeywordCall, utils.RETURN_CLASSES.return_class, Break, Continue))
        ):
            return
        min_possible = tokens_length(node.header.tokens) + tokens_length(node.body[0].tokens[1:]) + 2
        if min_possible > self.max_width:
            return
        token = node.header.get_token(node.header.type)
        self.report(
            node=node,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
            sev_threshold_value=min_possible,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Replace the IF block with an inline IF."""
        node = diag.node
        if node is None:
            return None
        converter = InlineIfConverter(separator="    ", indent="    ", line_length=self.max_width)
        indent = node.header.tokens[0].value
        result = converter.to_inline(node, indent)
        if result is node:  # the inline IF would be longer than the limit
            return None
        statements = result if isinstance(result, tuple) else (result,)
        replacement = "".join(StatementLinesCollector(statement).text for statement in statements)
        return Fix(
            edits=[
                TextEdit.replace_lines(
                    rule_id=self.rule_id,
                    rule_name=self.name,
                    start_line=node.lineno,
                    end_line=node.end_lineno,
                    replacement=replacement,
                )
            ],
            message="Replace IF block with an inline IF",
            applicability=FixApplicability.SAFE,
        )


class UnreachableCodeRule(Rule):
    """
    Unreachable code.

    Detects the unreachable code after ``RETURN``, ``BREAK`` or ``CONTINUE`` statements.

    For example:

        *** Keywords ***
        Example Keyword
            FOR    ${animal}    IN    cat    dog
                IF    '${animal}' == 'cat'
                    CONTINUE
                    Log  ${animal}  # unreachable log
                END
                BREAK
                Log    Unreachable log
            END
            RETURN
            Log    Unreachable log

    """

    name = "unreachable-code"
    rule_id = "MISC10"
    message = "Unreachable code after {statement} statement"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL,
        issue_type=sonar_qube.SonarQubeIssueType.BUG,
    )
    deprecated_names = ("0917",)

    def check(self, node: Block) -> None:
        """Report statements placed after RETURN, BREAK or CONTINUE."""
        if not self.enabled:
            return
        statement_node = None
        for child in node.body:
            if isinstance(child, (utils.RETURN_CLASSES.return_class, Break, Continue)):
                statement_node = child
            elif not isinstance(child, (EmptyLine, Comment, Teardown)) and statement_node is not None:
                token = statement_node.data_tokens[0]
                reported_node = child.header if hasattr(child, "header") else child
                code_after_statement = reported_node.data_tokens[0]
                self.report(
                    statement=token.value,
                    node=reported_node,
                    col=code_after_statement.col_offset + 1,
                    end_col=reported_node.end_col_offset,
                )
                statement_node = None


class MultilineInlineIfRule(Rule):
    """
    Multi-line inline IF.

    It's allowed to create ``inline IF`` that spans multiple lines, but it should be avoided,
    since it decreases readability. Try to use normal ``IF``/``ELSE`` instead.

    Incorrect code example:

        *** Keywords ***
        Keyword
            IF  ${condition}  Log  hello
            ...    ELSE       Log  hi!

    Correct code:

        *** Keywords ***
        Keyword
            IF  ${condition}    Log  hello     ELSE    Log  hi!

    or IF block can be used:

        *** Keywords ***
        Keyword
            IF  ${condition}
                Log  hello
            ELSE
                Log  hi!
            END

    Use the ``InlineIf`` formatter (``robocop format``) to reformat the inline IF.

    """

    name = "multiline-inline-if"
    rule_id = "MISC11"
    message = "Inline IF split to multiple lines"
    severity = RuleSeverity.WARNING
    version = ">=5.0"
    added_in_version = "3.1.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0918",)

    def check(self, node: If) -> None:
        if node.lineno == node.end_lineno:
            return
        if_header = node.header.data_tokens[0]
        self.report(
            node=node,
            col=if_header.col_offset + 1,
            end_lineno=node.end_lineno,
            end_col=node.end_col_offset,
        )


class UnnecessaryStringConversionRule(Rule):  # TODO: Not used atm, see if it was deprecated before
    """
    Variable in the condition has unnecessary string conversion.

    Expressions in Robot Framework are evaluated using Python's eval function. When a variable is used
    in the expression using the normal ``${variable}`` syntax, its value is replaced before the expression
    is evaluated. For example, with the following expression:

        *** Test Cases ***
        Check if schema was uploaded
            Upload Schema    schema.avsc
            Check If File Exist In SFTP    schema.avsc

        *** Keywords ***
        Upload Schema
            [Arguments]    ${filename}
            IF    ${filename} == 'default'
                ${filename}    Get Default Upload Path
            END
            Send File To SFTP Root   ${filename}

    "${filename}" will be replaced by "schema.avsc":

        IF    schema.avsc == 'default'

    "schema.avsc" will not be recognized as Python variable. That's why you need to quote it:

        IF    '${filename}' == 'default'

    However, it introduces unnecessary string conversion and can mask difference in the type. For example:

        ${numerical}    Set Variable    10  # ${numerical} is actually string 10, not integer 10
        IF    "${numerical}" == "10"

    You can use  ``$variable`` syntax instead:

        IF    $numerical == 10

    It will put the actual variable in the evaluated expression without converting it to string.

    """

    name = "unnecessary-string-conversion"
    rule_id = "MISC12"
    message = "Variable '{name}' in '{block_name}' condition has unnecessary string conversion"
    severity = RuleSeverity.INFO
    deprecated = True
    version = ">=4.0"
    added_in_version = "4.0.0"
    deprecated_names = ("0923",)


class ExpressionCanBeSimplifiedRule(Rule):
    """
    Condition can be simplified.

    Evaluated expression can be simplified.

    Incorrect code example:

        *** Keywords ***
        Click On Element
            [Arguments]    ${locator}
            IF    ${is_element_visible}==${TRUE}    RETURN
            ${is_element_enabled}    Set Variable    ${TRUE}
            WHILE    ${is_element_enabled} != ${TRUE}
                ${is_element_enabled}    Get Element Status    ${locator}
            END
            Click    ${locator}

    Correct code:

        *** Keywords ***
        Click On Element
            [Arguments]    ${locator}
            IF    ${is_element_visible}    RETURN
            ${is_element_enabled}    Set Variable    ${FALSE}
            WHILE    not ${is_element_enabled}
                ${is_element_enabled}    Get Element Status    ${locator}
            END
            Click    ${locator}

    Comparisons to empty sequences (lists, dicts, sets), empty string or ``0`` can be also simplified:

        *** Test Cases ***
        Check conditions
            Should Be True     ${list} == []  # equivalent of 'not ${list}'
            Should Be True     ${string} != ""  # equivalent of '${string}'
            Should Be True     len(${sequence}))  # equivalent of '${sequence}'

    """

    name = "expression-can-be-simplified"
    rule_id = "MISC13"
    message = "'{block_name}' condition can be simplified"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "4.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0924",)

    def check(
        self, condition_token: Token, node_name: str, left_side: str, variable: str, right_side: str, position: int
    ) -> None:
        """Check if the right side of the equation can be simplified."""
        if not right_side:
            return
        normalized = right_side.lower().lstrip()  # ' == ${TRUE}' -> '== ${true}'
        if len(normalized) < 3:
            if normalized == ")" and left_side.endswith("len("):
                self.report(
                    block_name=node_name,
                    node=condition_token,
                    col=position - len("len("),
                    end_col=position + len(variable) + 1,
                )
            return
        equation = normalized[:2]  # '=='
        compared_value = normalized[2:].lstrip()  # '${true}'
        if equation not in COMPARISON_SIGNS:
            return
        if compared_value in EMPTY_COMPARISON:
            self.report(
                block_name=node_name,
                node=condition_token,
                col=position,
                end_col=position + len(variable) + len(right_side),
            )


class MisplacedNegativeConditionRule(FixableRule):
    """
    The position of not operator can be changed for better readability.

    Incorrect code example:

        *** Keywords ***
        Check Unmapped Codes
            ${codes}    Get Codes From API
            IF    not ${codes} is None
                FOR    ${code}    IN    @{codes}
                    Validate Single Code    ${code}
                END
            ELSE
                Fail    Did not receive codes from API.
            END

    Correct code:

        *** Keywords ***
        Check Unmapped Codes
            ${codes}    Get Codes From API
            IF    ${codes} is not None
                FOR    ${code}    IN    @{codes}
                    Validate Single Code    ${code}
                END
            ELSE
                Fail    Did not receive codes from API.
            END

    The condition can be rewritten automatically with the ``--fix`` option.

    """

    name = "misplaced-negative-condition"
    rule_id = "MISC14"
    message = "'{block_name}' condition '{original_condition}' can be rewritten to '{proposed_condition}'"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "4.0.0"
    fix_availability = FixAvailability.SOMETIMES
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0925",)

    def check(self, condition_token: Token, node_name: str, left_side: str, variable: str, right_side: str) -> None:
        """
        Check if the condition contains misplaced not.

        An example of a misplaced condition would be 'not ${variable} is None'.
        """
        if not (left_side.endswith("not ") and right_side.startswith(" is ")):
            return
        right_tokens = right_side.split(" ")
        orig_right_side = " ".join(right_tokens[1:3])
        self.report(
            block_name=node_name,
            original_condition=f"not {variable} {orig_right_side}",
            proposed_condition=f"{variable} is not {right_tokens[2]}",
            node=condition_token,
            col=condition_token.col_offset + 1,
            end_col=condition_token.end_col_offset + 1,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Move the ``not`` operator from the left side of the condition to the comparison itself."""
        original = str(diag.reported_arguments["original_condition"])
        proposed = str(diag.reported_arguments["proposed_condition"])
        parts = original.split(" ")
        if len(parts) != NEGATIVE_CONDITION_PARTS or not all(parts) or parts[-1] == "not":
            return None  # unexpected condition, we cannot reliably rewrite it
        line = source_lines[diag.range.start.line - 1]
        start = diag.range.start.character - 1
        end = diag.range.end.character - 1
        condition = line[start:end]
        if condition.count(original) != 1:
            return None
        offset = condition.index(original)
        if condition[:offset].endswith("not "):
            return None  # double negation, the intention is not clear
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=diag.range.start.line,
            start_col=start + offset + 1,
            end_line=diag.range.start.line,
            end_col=start + offset + len(original) + 1,
            replacement=proposed,
        )
        return Fix(
            edits=[edit],
            message=f"Rewrite '{original}' to '{proposed}'",
            applicability=FixApplicability.SAFE,
        )


def find_unspaced_operators(condition: str) -> list[tuple[str, int]]:
    """
    Find comparison operators that are missing surrounding whitespace.

    Returns a list of ``(operator, index)`` tuples where ``index`` is the 0-based position of the operator inside
    the condition string. Operators found inside string literals are ignored to avoid false positives.
    """
    found: list[tuple[str, int]] = []
    quote: str | None = None
    index = 0
    length = len(condition)
    while index < length:
        char = condition[index]
        if quote is not None:
            if char == quote:
                quote = None
            index += 1
            continue
        if char in "\"'":
            quote = char
            index += 1
            continue
        operator = next((op for op in COMPARISON_OPERATORS if condition.startswith(op, index)), None)
        if operator is None:
            index += 1
            continue
        end = index + len(operator)
        space_before = index == 0 or condition[index - 1] == " "
        space_after = end >= length or condition[end] == " "
        if not (space_before and space_after):
            found.append((operator, index))
        index = end
    return found


class NotEnoughWhitespaceAroundOperatorRule(FixableRule):
    """
    Not enough whitespace around a comparison operator.

    Comparison operators (``==``, ``!=``, ``>``, ``<``, ``>=``, ``<=``) used in conditions are easier to read
    when they are surrounded by spaces. The rule inspects conditions of ``IF`` and ``WHILE`` blocks together with
    the conditions passed to the BuiltIn keywords that evaluate an expression
    (such as ``Should Be True`` or ``Skip If``).

    Incorrect code example:

        *** Test Cases ***
        Test
            IF    ${variable}==5
                Log    Robocop
            END
            WHILE    ${counter}>=${LIMIT}
                ${counter}    Evaluate    ${counter} + 1
            END
            Should Be True    ${left}!=${right}

    Correct code:

        *** Test Cases ***
        Test
            IF    ${variable} == 5
                Log    Robocop
            END
            WHILE    ${counter} >= ${LIMIT}
                ${counter}    Evaluate    ${counter} + 1
            END
            Should Be True    ${left} != ${right}

    The missing whitespace can be added automatically with the ``--fix`` option.

    """

    name = "not-enough-whitespace-around-operator"
    rule_id = "MISC16"
    message = "Not enough whitespace around '{operator}' operator in '{block_name}' condition"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "9.0.0"
    fix_availability = FixAvailability.ALWAYS
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.FORMATTED,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )

    def check(self, condition_token: Token, node_name: str, condition: str) -> None:
        """Report comparison operators used in the condition without surrounding whitespace."""
        for operator, index in find_unspaced_operators(condition):
            col = condition_token.col_offset + index + 1
            self.report(
                operator=operator,
                block_name=node_name,
                node=condition_token,
                col=col,
                end_col=col + len(operator),
            )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """Insert the missing spaces around the comparison operator."""
        operator = str(diag.reported_arguments["operator"])
        line = source_lines[diag.range.start.line - 1]
        start = diag.range.start.character - 1
        end = diag.range.end.character - 1
        if line[start:end] != operator:
            return None
        space_before = start == 0 or line[start - 1] == " "
        space_after = end >= len(line) or line[end] == " "
        replacement = f"{'' if space_before else ' '}{operator}{'' if space_after else ' '}"
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=diag.range.start.line,
            start_col=start + 1,
            end_line=diag.range.start.line,
            end_col=end + 1,
            replacement=replacement,
        )
        return Fix(
            edits=[edit],
            message=f"Add missing whitespace around '{operator}' operator",
            applicability=FixApplicability.SAFE,
        )


class DisablerNotUsedRule(FixableRule):
    """
    Robocop disabler directive is not used.

    Overlapping disablers, code that was already fixed or rules that are disabled globally do not need rule disablers.

    Rule violation examples:

        *** Keywords ***
        Log To Page
            ${email}    Get Email  # robocop: off=unused-variable
            Log    ${email}
            FOR    ${locator}    IN    @{email_locators}
                # robocop: off
                # robocop: off=some-rule
                Fill Text    ${locator}
            END

    In the above examples we disable unused-variable rule, but no violation is raised for this line.
    Also, we define disablers for all rules and some-rule in FOR loop, and all rules disabler overlaps second disabler
    which is never used.

    Unused disablers can be removed automatically with the ``--fix`` option. Only the unused rule name is removed
    if the directive disables more rules. Disablers that share the comment with any other content are not
    removed automatically.

    """

    name = "unused-disabler"
    rule_id = "MISC15"
    message = "Disabler directive found for '{rule_name}' rule(s) but no violation found"
    severity = RuleSeverity.INFO
    added_in_version = "6.8.0"
    fix_availability = FixAvailability.SOMETIMES
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:
        """
        Remove the unused disabler directive.

        Only the reported rule name is removed if the directive disables more rules. Otherwise, the whole comment
        with the directive is removed. Directives followed by any other content in the same line are not fixed,
        since removing them could change the meaning of the remaining content.
        """
        lineno = diag.range.start.line
        line = source_lines[lineno - 1]
        start_index = diag.range.start.character - 1
        end_index = min(diag.range.end.character - 1, len(line.rstrip()))
        if start_index < 0 or end_index <= start_index:
            return None
        comment_start = start_index if line[start_index] == "#" else line.rfind("#", 0, start_index)
        if comment_start == -1:
            return None
        if line[comment_start + 1 : start_index].strip() or line[end_index:].strip():
            return None  # other content in the same comment
        directive = line[start_index:end_index]
        rule_name = str(diag.reported_arguments["rule_name"])
        if "=" in directive:
            prefix, _, rules = directive.partition("=")
            rule_names = [name.strip() for name in rules.split(",") if name.strip()]
            if rule_name not in rule_names:  # directive contains extra content we cannot safely remove
                return None
            if len(rule_names) > 1:
                remaining = [name for name in rule_names if name != rule_name]
                new_line = f"{line[:start_index]}{prefix}={','.join(remaining)}{line[end_index:]}"
                # whole line is replaced so that only one rule name is removed in a single pass
                edit = TextEdit.replace_lines(self.rule_id, self.name, lineno, lineno, new_line)
                return Fix(
                    edits=[edit],
                    message=f"Remove unused '{rule_name}' from the disabler directive",
                    applicability=FixApplicability.SAFE,
                )
        message = f"Remove unused disabler directive for '{rule_name}' rule(s)"
        return self._remove_comment_fix(lineno, line, comment_start, message)

    def _remove_comment_fix(self, lineno: int, line: str, comment_start: int, message: str) -> Fix:
        """Remove the comment from the line, or the whole line if it contains only the comment."""
        if not line[:comment_start].strip():
            return remove_lines_fix(self, lineno, lineno, message)
        replacement = line[:comment_start].rstrip() + line[len(line.rstrip()) :]
        edit = TextEdit.replace_lines(self.rule_id, self.name, lineno, lineno, replacement)
        return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


@dataclass
class CachedVariable:
    name: str
    token: Token
    is_used: bool
    current_scopy_only: bool = False


class SectionVariablesCollector(ast.NodeVisitor):
    """Visitor for collecting all variables in the suite"""

    def __init__(self) -> None:
        self.section_variables: dict[str, CachedVariable] = {}

    def visit_Variable(self, node: Variable) -> None:
        if node.errors:
            return
        var_token = node.get_token(Token.VARIABLE)
        variable_match = search_variable(var_token.value, ignore_errors=True)
        name = utils.remove_variable_type_conversion(variable_match.base)
        normalized = utils.normalize_robot_name(name)
        self.section_variables[normalized] = CachedVariable(variable_match.name, var_token, is_used=False)
