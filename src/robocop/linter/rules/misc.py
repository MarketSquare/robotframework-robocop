"""Miscellaneous checkers"""

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.blocks import For, TestCaseSection
from robot.parsing.model.statements import Arguments, KeywordCall, Teardown
from robot.variables.search import search_variable

from robocop.linter.diagnostics import Diagnostic
from robocop.source_file import SourceFile

try:
    from robot.api.parsing import Comment, EmptyLine, If, Variable
except ImportError:
    from robot.parsing.model.statements import Comment, EmptyLine, Variable
try:
    from robot.api.parsing import Break, Continue, InlineIfHeader
except ImportError:
    InlineIfHeader, Break, Continue = None, None, None
try:  # RF 7+
    from robot.api.parsing import Var
except ImportError:
    Var = None  # type: ignore[assignment, misc]

from robocop.linter import sonar_qube
from robocop.linter.rules import (
    AfterRunChecker,
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
    VisitorChecker,
    arguments,
    deprecated,
    typing,
    variables,
)
from robocop.linter.utils import misc as utils
from robocop.parsing.variables import VariableMatches
from robocop.version_handling import INLINE_IF_SUPPORTED, ROBOT_VERSION

if TYPE_CHECKING:
    from robocop.linter.utils.disablers import DisablersFinder


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


class EmptyReturnRule(Rule):
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


class InconsistentAssignmentRule(Rule):
    """
    Not consistent assignment sign in the file.

    Use only one type of assignment sign in a file.

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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0909",)


class InconsistentAssignmentInVariablesRule(Rule):
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
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0910",)


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


class InlineIfCanBeUsedRule(Rule):
    """
    IF can be replaced with inline IF.

    Short and simple ``IF`` statements can be replaced with ``inline IF``.

    Following ``IF``:

        IF    $condition
            BREAK
        END

    can be replaced with:

        IF    $condition    BREAK


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


class MisplacedNegativeConditionRule(Rule):
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

    """

    name = "misplaced-negative-condition"
    rule_id = "MISC14"
    message = "'{block_name}' condition '{original_condition}' can be rewritten to '{proposed_condition}'"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "4.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )
    deprecated_names = ("0925",)


class DisablerNotUsedRule(Rule):
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

    """

    name = "unused-disabler"
    rule_id = "MISC15"
    message = "Disabler directive found for '{rule_name}' rule(s) but no violation found"
    severity = RuleSeverity.INFO
    added_in_version = "6.8.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL,
        issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL,
    )


class ReturnChecker(VisitorChecker):
    """Checker for [Return] and Return From Keyword violations."""

    keyword_after_return: KeywordAfterReturnRule
    empty_return: EmptyReturnRule

    def visit_Keyword(self, node) -> None:  # noqa: N802
        return_setting_node = None
        keyword_after_return = False
        return_from = False
        error = ""
        for child in node.body:
            if isinstance(child, utils.RETURN_CLASSES.return_setting_class):
                return_setting_node = child
                error = (
                    "[Return] is not defined at the end of keyword. "
                    "Note that [Return] does not quit from keyword but only set variables to be returned"
                )
                if not child.values:
                    token = child.data_tokens[0]
                    self.report(
                        self.empty_return,
                        node=child,
                        col=token.col_offset + 1,
                        end_col=token.col_offset + len(token.value),
                    )
            elif not isinstance(child, (EmptyLine, Comment, Teardown)):
                if return_setting_node is not None:
                    keyword_after_return = True

            if isinstance(child, KeywordCall):
                if return_from:
                    keyword_after_return = True
                    return_setting_node = child
                    error = "Keyword call after 'Return From Keyword'"
                elif utils.normalize_robot_name(child.keyword, remove_prefix="builtin.") == "returnfromkeyword":
                    return_from = True
        if keyword_after_return:
            token = return_setting_node.data_tokens[0]
            self.report(
                self.keyword_after_return,
                error_msg=error,
                node=token,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )
        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword  # noqa: N815


class UnreachableCodeChecker(VisitorChecker):
    """Checker for unreachable code after RETURN, BREAK or CONTINUE statements."""

    unreachable_code: UnreachableCodeRule

    def visit_Keyword(self, node) -> None:  # noqa: N802
        statement_node = None

        for child in node.body:
            if isinstance(child, (utils.RETURN_CLASSES.return_class, Break, Continue)):
                statement_node = child
            elif not isinstance(child, (EmptyLine, Comment, Teardown)) and statement_node is not None:
                token = statement_node.data_tokens[0]
                if hasattr(child, "header"):
                    child = child.header
                code_after_statement = child.data_tokens[0]
                self.report(
                    self.unreachable_code,
                    statement=token.value,
                    node=child,
                    col=code_after_statement.col_offset + 1,
                    end_col=child.end_col_offset,
                )
                statement_node = None

        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword  # noqa: N815


class NestedForLoopsChecker(VisitorChecker):  # TODO: merge
    """
    Checker for not supported nested FOR loops.

    Deprecated in RF 4.0
    """

    nested_for_loop: NestedForLoopRule

    def visit_ForLoop(self, node) -> None:  # noqa: N802
        # For RF 4.0 node is "For" but we purposely don't visit it because nested for loop is allowed in 4.0
        for child in node.body:
            if child.type == "FOR":
                token = child.get_token(Token.FOR)
                self.report(
                    self.nested_for_loop,
                    node=child,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )


class IfBlockCanBeUsed(VisitorChecker):
    """
    Checker for potential IF block usage in Robot Framework 4.0

    Run Keyword variants (Run Keyword If, Run Keyword Unless) can be replaced with IF in RF 4.0
    """

    if_can_be_used: deprecated.IfCanBeUsedRule
    run_keyword_variants = {"runkeywordif", "runkeywordunless"}

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if not node.keyword:
            return
        if utils.normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.run_keyword_variants:
            col = utils.keyword_col(node)
            self.report(
                self.if_can_be_used,
                run_keyword=node.keyword,
                node=node,
                col=col,
                end_col=col + len(node.keyword),
            )


class ConsistentAssignmentSignChecker(VisitorChecker):
    """
    Checker for inconsistent assignment signs.

    By default, this checker will try to autodetect most common assignment sign (separately for ``*** Variables ***``
    section and ``*** Test Cases ***``, ``*** Keywords ***`` sections) and report any inconsistent type of sign in
    particular file.

    To force one type of sign type you can configure two rules:

        robocop check --configure inconsistent-assignment.assignment_sign_type={sign_type}
        robocop check --configure inconsistent-assignment-in-variables.assignment_sign_type={sign_type}

    You can choose between following signs:

    - 'autodetect' (default),
    - 'none',
    - 'equal_sign' (``=``)
    - 'space_and_equal_sign' (`` =``).

    """

    inconsistent_assignment: InconsistentAssignmentRule
    inconsistent_assignment_in_variables: InconsistentAssignmentInVariablesRule

    def __init__(self) -> None:
        self.keyword_expected_sign_type = None
        self.variables_expected_sign_type = None
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.keyword_expected_sign_type = self.inconsistent_assignment.assignment_sign_type
        self.variables_expected_sign_type = self.inconsistent_assignment_in_variables.assignment_sign_type
        if "autodetect" in [
            self.keyword_expected_sign_type,
            self.variables_expected_sign_type,
        ]:
            auto_detector = self.auto_detect_assignment_sign(node)
            if self.keyword_expected_sign_type == "autodetect":
                self.keyword_expected_sign_type = auto_detector.keyword_most_common
            if self.variables_expected_sign_type == "autodetect":
                self.variables_expected_sign_type = auto_detector.variables_most_common
        self.generic_visit(node)

    def visit_KeywordCall(self, node):  # noqa: N802
        if self.keyword_expected_sign_type is None or not node.keyword:
            return None
        if node.assign:  # if keyword returns any value
            assign_tokens = node.get_tokens(Token.ASSIGN)
            self.check_assign_type(
                assign_tokens[-1],
                self.keyword_expected_sign_type,
                self.inconsistent_assignment,
            )
        return node

    def visit_VariableSection(self, node):  # noqa: N802
        if self.variables_expected_sign_type is None:
            return None
        for child in node.body:
            if not isinstance(child, Variable) or child.errors:
                continue
            var_token = child.get_token(Token.VARIABLE)
            self.check_assign_type(
                var_token,
                self.variables_expected_sign_type,
                self.inconsistent_assignment_in_variables,
            )
        return node

    def check_assign_type(self, token, expected, issue_name) -> None:
        sign = utils.AssignmentTypeDetector.get_assignment_sign(token.value)
        if sign != expected:
            self.report(
                issue_name,
                expected_sign=expected,
                actual_sign=sign,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )

    @staticmethod
    def auto_detect_assignment_sign(node):
        auto_detector = utils.AssignmentTypeDetector()
        auto_detector.visit(node)
        return auto_detector


class EmptyVariableChecker(VisitorChecker):
    """Checker for variables without value."""

    empty_variable: variables.EmptyVariableRule

    def __init__(self) -> None:
        self.visit_var_section = False
        self.visit_var = False
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        variable_source = self.empty_variable.variable_source
        self.visit_var_section = "section" in variable_source
        self.visit_var = "var" in variable_source
        self.generic_visit(node)

    def visit_VariableSection(self, node) -> None:  # noqa: N802
        if self.visit_var_section:
            self.generic_visit(node)

    def visit_KeywordSection(self, node) -> None:  # noqa: N802
        if self.visit_var:
            self.generic_visit(node)

    visit_TestCaseSection = visit_KeywordSection  # noqa: N815

    def visit_Variable(self, node) -> None:  # noqa: N802
        if node.errors:
            return
        if not node.value:  # catch variable declaration without any value
            self.report(self.empty_variable, node=node, end_col=node.end_col_offset)
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    self.empty_variable,
                    node=token,
                    lineno=token.lineno,
                    col=1,
                    end_col=token.end_col_offset + 1,
                )

    def visit_Var(self, node) -> None:  # noqa: N802
        if node.errors:
            return
        if not node.value:  # catch variable declaration without any value
            first_data = node.data_tokens[0]
            self.report(
                self.empty_variable,
                node=first_data,
                col=first_data.col_offset + 1,
                end_col=first_data.end_col_offset + 1,
            )
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    self.empty_variable,
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )


class ResourceFileChecker(VisitorChecker):
    """Checker for resource files."""

    can_be_resource_file: CanBeResourceFileRule

    def visit_File(self, node) -> None:  # noqa: N802
        source = self.source_file.path.name
        if source:
            extension = Path(source).suffix
            file_name = Path(source).stem
            if (
                ".resource" not in extension
                and "__init__" not in file_name
                and node.sections
                and not any(isinstance(section, TestCaseSection) for section in node.sections)
            ):
                self.report(
                    self.can_be_resource_file,
                    file_name=Path(source).name,
                    file_name_stem=file_name,
                    node=node,
                )


class IfChecker(VisitorChecker):
    """Checker for IF blocks"""

    if_can_be_merged: IfCanBeMergedRule
    inline_if_can_be_used: InlineIfCanBeUsedRule
    multiline_inline_if: MultilineInlineIfRule

    def visit_TestCase(self, node) -> None:  # noqa: N802
        if node.errors:
            return
        self.check_adjacent_ifs(node)

    visit_For = visit_If = visit_Keyword = (  # noqa: N815
        visit_TestCase  # TODO: While, Try Except?
    )

    @staticmethod
    def is_inline_if(node):
        return isinstance(node.header, InlineIfHeader)

    def check_adjacent_ifs(self, node) -> None:
        previous_if = None
        for child in node.body:
            if isinstance(child, If):
                if child.header.errors:
                    continue
                self.check_whether_if_should_be_inline(child)
                if previous_if and child.header and self.compare_conditions(child, previous_if):
                    token = child.header.get_token(child.header.type)
                    self.report(
                        self.if_can_be_merged,
                        line=previous_if.lineno,
                        node=token,
                        col=token.col_offset + 1,
                        end_col=token.end_col_offset + 1,
                    )
                previous_if = child
            elif not isinstance(child, (Comment, EmptyLine)):
                previous_if = None
        self.generic_visit(node)

    def compare_conditions(self, if_node, other_if_node):
        if not self.compare_assign_tokens(if_node, other_if_node):
            return False
        while if_node is not None and other_if_node is not None:
            if if_node.condition != other_if_node.condition:
                return False
            if_node = if_node.orelse
            other_if_node = other_if_node.orelse
        return if_node is None and other_if_node is None

    @staticmethod
    def normalize_var_name(name):
        return name.lower().replace("_", "").replace(" ", "").replace("=", "")

    def compare_assign_tokens(self, if_node, other_if_node):
        assign_1 = getattr(if_node, "assign", None)
        assign_2 = getattr(other_if_node, "assign", None)
        if assign_1 is None or assign_2 is None:
            return all(assign is None for assign in (assign_1, assign_2))
        if len(assign_1) != len(assign_2):
            return False
        for var1, var2 in zip(assign_1, assign_2, strict=False):
            if self.normalize_var_name(var1) != self.normalize_var_name(var2):
                return False
        return True

    @staticmethod
    def tokens_length(tokens):
        return sum(len(token.value) for token in tokens)

    def check_whether_if_should_be_inline(self, node) -> None:
        if not INLINE_IF_SUPPORTED:
            return
        if self.is_inline_if(node):
            if node.lineno != node.end_lineno:
                if_header = node.header.data_tokens[0]
                self.report(
                    self.multiline_inline_if,
                    node=node,
                    col=if_header.col_offset + 1,
                    end_lineno=node.end_lineno,
                    end_col=node.end_col_offset,
                )
            return
        if (
            len(node.body) != 1
            or node.orelse  # TODO: it could still report with orelse? if short enough
            # IF with one branch and assign require ELSE to be valid, better to ignore it
            or getattr(node.body[0], "assign", None)
            or not isinstance(node.body[0], (KeywordCall, utils.RETURN_CLASSES.return_class, Break, Continue))  # type: ignore[arg-type]
        ):
            return
        min_possible = self.tokens_length(node.header.tokens) + self.tokens_length(node.body[0].tokens[1:]) + 2
        if min_possible > self.inline_if_can_be_used.max_width:
            return
        token = node.header.get_token(node.header.type)
        self.report(
            self.inline_if_can_be_used,
            node=node,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
            sev_threshold_value=min_possible,
        )


class LoopStatementsChecker(VisitorChecker):
    """Checker for loop keywords and statements such as CONTINUE or Exit For Loop"""

    statement_outside_loop: StatementOutsideLoopRule
    for_keyword = {
        "continueforloop",
        "continueforloopif",
        "exitforloop",
        "exitforloopif",
    }

    def __init__(self) -> None:
        self.loops = 0
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.loops = 0
        self.generic_visit(node)

    def visit_For(self, node) -> None:  # noqa: N802
        self.loops += 1
        self.generic_visit(node)
        self.loops -= 1

    visit_While = visit_For  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        if node.errors or self.loops:
            return
        if utils.normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.for_keyword:
            col = utils.keyword_col(node)
            self.report(
                self.statement_outside_loop,
                name=f"'{node.keyword}'",
                statement_type="keyword",
                node=node,
                col=col,
                end_col=col + len(node.keyword),
            )

    def visit_Continue(self, node) -> None:  # noqa: N802
        self.check_statement_in_loop(node, "CONTINUE")  # type: ignore[arg-type]

    def visit_Break(self, node) -> None:  # noqa: N802
        self.check_statement_in_loop(node, "BREAK")  # type: ignore[arg-type]

    def visit_Error(self, node) -> None:  # noqa: N802
        """Support for RF >= 6.1"""
        for error_token in node.get_tokens(Token.ERROR):
            if "is not allowed in this context" in error_token.error:
                self.report(
                    self.statement_outside_loop,
                    name=error_token.value,
                    statement_type="statement",
                    node=node,
                    col=error_token.col_offset + 1,
                    end_col=error_token.end_col_offset + 1,
                )

    def check_statement_in_loop(self, node, token_type) -> None:
        if self.loops or (node.errors and f"{token_type} can only be used inside a loop." not in node.errors):
            return
        error_token = node.get_token(token_type)
        self.report(
            self.statement_outside_loop,
            name=token_type,
            statement_type="statement",
            node=node,
            col=error_token.col_offset + 1,
            end_col=error_token.end_col_offset + 1,
        )


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

    def visit_Variable(self, node) -> None:
        if node.errors:
            return
        var_token = node.get_token(Token.VARIABLE)
        variable_match = search_variable(var_token.value, ignore_errors=True)
        name = utils.remove_variable_type_conversion(variable_match.base)
        normalized = utils.normalize_robot_name(name)
        self.section_variables[normalized] = CachedVariable(variable_match.name, var_token, is_used=False)


class UnusedVariablesChecker(VisitorChecker):
    unused_argument: arguments.UnusedArgumentRule
    unused_variable: variables.UnusedVariableRule
    argument_overwritten_before_usage: arguments.ArgumentOverwrittenBeforeUsageRule
    variable_overwritten_before_usage: variables.VariableOverwrittenBeforeUsageRule

    _ESCAPED_VAR_PATTERN = re.compile(r"\$([A-Za-z_]\w*)")
    _VARIABLE_NAME_PATTERN = re.compile(r"\w+")

    def __init__(self) -> None:
        self.arguments: dict[str, CachedVariable] = {}
        self.variables: list[dict[str, CachedVariable]] = [
            {}
        ]  # variables are list of scope-dictionaries, to support IF branches
        self.current_if_variables: list[dict[str, CachedVariable]] = []
        self.section_variables: dict[str, CachedVariable] = {}
        self.used_in_scope: list[set] = []  # variables that were used in current FOR/WHILE loop
        self.ignore_overwriting = False  # temporarily ignore overwriting, e.g. in FOR loops
        self.in_loop = False  # if we're in the loop we need to check whole scope for unused-variable
        self.test_or_task_section = False
        self.branch_level = 0  # if we're inside any if branch, it will be > 0
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.test_or_task_section = False
        section_variables = SectionVariablesCollector()
        section_variables.visit(node)
        self.section_variables = section_variables.section_variables
        self.generic_visit(node)
        self.report_not_used_section_variables()

    def report_not_used_section_variables(self) -> None:
        if not self.test_or_task_section:
            return
        ignored = self.get_ignored_variable_names()
        for variable in self.section_variables.values():
            should_ignore = variable.is_used or utils.normalize_robot_var_name(variable.name) in ignored
            if not should_ignore:
                self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)

    def get_ignored_variable_names(self) -> set[str]:
        """Get normalized set of variable names to ignore from the ignore parameter."""
        ignore_config = self.unused_variable.ignore
        if not ignore_config:
            return set()
        return {utils.normalize_robot_name(name.strip()) for name in ignore_config.split(",")}

    def visit_TestCaseSection(self, node) -> None:  # noqa: N802
        self.test_or_task_section = True
        self.generic_visit(node)

    visit_TaskSection = visit_TestCaseSection  # noqa: N815

    def visit_TestCase(self, node) -> None:  # noqa: N802
        self.variables = [{}]
        self.generic_visit(node)
        self.check_unused_variables()

    def visit_Keyword(self, node) -> None:  # noqa: N802
        self.arguments = {}
        self.variables = [{}]
        name_token = node.header.get_token(Token.KEYWORD_NAME)
        self.parse_embedded_arguments(name_token)
        # iterating there instead of using visit_Arguments, so we don't check keywords without arguments
        for statement in node.body:
            if isinstance(statement, Arguments):
                self.parse_arguments(statement)
        self.generic_visit(node)
        for arg in self.arguments.values():
            if not arg.is_used:
                value, *_ = arg.token.value.split("=", maxsplit=1)
                self.report_arg_or_var_rule(self.unused_argument, arg.token, value)
        self.check_unused_variables()
        self.arguments = {}

    def check_unused_variables(self) -> None:
        for scope in self.variables:
            self.check_unused_variables_in_scope(scope)

    def check_unused_variables_in_scope(self, scope) -> None:
        for variable in scope.values():
            if not variable.is_used:
                self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)

    def report_arg_or_var_rule(self, rule, token, value=None) -> None:
        if value is None:
            value = token.value
        self.report(
            rule,
            name=value,
            node=token,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.col_offset + len(value) + 1,
        )

    def add_argument(self, argument, normalized_name, token) -> None:
        self.arguments[normalized_name] = CachedVariable(argument, token, is_used=False)

    def parse_arguments(self, node) -> None:
        """Store arguments from [Arguments]. Ignore @{args} and &{kwargs}, strip default values."""
        if node.errors:
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            if arg.value[0] in ("@", "&"):  # ignore *args and &kwargs
                continue
            arg_name, default_value = utils.split_argument_default_value(arg.value)
            if default_value:
                self.find_not_nested_variable(default_value, can_be_escaped=False)
            base_name = arg_name[2:-1]
            name = utils.remove_variable_type_conversion(base_name)
            name = utils.normalize_robot_name(name)
            self.add_argument(base_name, name, token=arg)
            # ${test.kws[0].msgs[${index}]} FIXME

    def parse_embedded_arguments(self, name_token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        if "$" not in name_token.value:
            return
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    normalized_name = utils.normalize_robot_var_name(token.value)
                    name, *_ = normalized_name.split(":", maxsplit=1)
                    self.add_argument(token.value, name, token=token)
        except VariableError:
            pass

    def visit_If(self, node):  # noqa: N802
        if node.header.errors:
            return
        self.branch_level += 1
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.variables.append({})
        for item in node.body:
            self.visit(item)
        if_variables = self.variables.pop()
        if node.orelse:
            self.visit_IfBranch(node.orelse)
        for token in node.header.get_tokens(Token.ASSIGN):
            self.handle_assign_variable(token)
        self.branch_level -= 1
        for scope in self.current_if_variables:
            for name, variable in scope.items():
                if name in if_variables:
                    if_variables[name].is_used = if_variables[name].is_used and variable.is_used
                    if not variable.is_used:
                        if_variables[name].token = variable.token
                else:
                    if_variables[name] = variable
        self.add_variables_from_if_to_scope(if_variables)
        self.current_if_variables = []

    def visit_IfBranch(self, node) -> None:  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.variables.append({})
        for child in node.body:
            self.visit(child)
        self.current_if_variables.append(self.variables.pop())
        if node.orelse:
            self.visit_IfBranch(node.orelse)

    def add_variables_from_if_to_scope(self, if_variables: dict[str, CachedVariable]) -> None:
        """
        Add all variables in the given IF branch to a common scope. If a variable is used already in the branch, it
        will also be marked as used.
        """
        if not self.variables:
            self.variables.append(if_variables)
            return
        for var_name, cached_var in if_variables.items():
            if var_name in self.variables[-1]:
                if cached_var.is_used:
                    self.variables[-1][var_name].is_used = True
            else:
                self.variables[-1][var_name] = cached_var

    def visit_LibraryImport(self, node) -> None:  # noqa: N802
        for token in node.get_tokens(Token.NAME, Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=False)

    visit_TestTags = visit_ForceTags = visit_Metadata = visit_DefaultTags = (  # noqa: N815
        visit_Variable  # noqa: N815
    ) = visit_ReturnStatement = visit_ReturnSetting = visit_Teardown = (  # noqa: N815
        visit_Timeout  # noqa: N815
    ) = visit_Return = visit_SuiteSetup = (  # noqa: N815  # noqa: N815
        visit_SuiteTeardown  # noqa: N815
    ) = visit_TestSetup = visit_TestTeardown = visit_Setup = (  # noqa: N815
        visit_ResourceImport  # noqa: N815
    ) = visit_VariablesImport = visit_Tags = (  # noqa: N815  # noqa: N815
        visit_Documentation  # noqa: N815
    ) = visit_LibraryImport

    def clear_variables_after_loop(self) -> None:
        """Remove used variables after the loop finishes."""
        for index, scope in enumerate(self.variables):
            self.variables[index] = {name: variable for name, variable in scope.items() if not variable.is_used}

    def revisit_variables_used_in_loop(self) -> None:
        """
        Due to the recursive nature of the loops, we need to revisit variables used in the loop again in case
        the variable defined in the further part of the loop was used.

        In case of nested FOR/WHILE loops, we're storing variables in separate stacks that are merged until we reach
        the outer END.

        For example:

            *** Keywords ***
            Use loop variable
                WHILE    ${True}
                    ${counter}    Update Counter    ${counter}
                END
        """
        top_stack = self.used_in_scope.pop()
        if self.used_in_scope:
            self.used_in_scope[-1] = self.used_in_scope[-1].union(top_stack)
        else:
            for name in top_stack:
                self._set_variable_as_used(name, self.variables[-1])

    def visit_While(self, node):  # noqa: N802
        if node.header.errors:
            return
        self.in_loop = True
        self.used_in_scope.append(set())
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        if node.limit:
            self.find_not_nested_variable(node.limit, can_be_escaped=False)
        self.generic_visit(node)
        self.in_loop = False
        self.revisit_variables_used_in_loop()
        self.clear_variables_after_loop()

    def visit_For(self, node):  # noqa: N802
        if getattr(node.header, "errors", None):
            return
        self.in_loop = True
        self.used_in_scope.append(set())
        self.ignore_overwriting = True
        for token in node.header.get_tokens(Token.ARGUMENT, "OPTION"):  # Token.Option does not exist for RF3 and RF4
            self.find_not_nested_variable(token.value, can_be_escaped=False)
        for token in node.header.get_tokens(Token.VARIABLE):
            self.handle_assign_variable(token, ignore_var_conversion=False)
        self.generic_visit(node)
        self.ignore_overwriting = False
        self.in_loop = False
        self.revisit_variables_used_in_loop()
        self.clear_variables_after_loop()

    visit_ForLoop = visit_For  # noqa: N815

    @staticmethod
    def try_assign(try_node) -> str:
        if ROBOT_VERSION.major < 7:
            return try_node.variable
        return try_node.assign

    def visit_Try(self, node):  # noqa: N802
        if node.errors or node.header.errors:
            return
        # first gather variables from the TRY node
        self.variables.append({})
        for item in node.body:
            self.visit(item)
        try_variables = self.variables.pop()
        branch_variables = []
        try_branch = node.next
        while try_branch:
            self.variables.append({})
            # variables in EXCEPT  ${error_pattern}
            for token in try_branch.header.get_tokens(Token.ARGUMENT, Token.OPTION):
                self.find_not_nested_variable(token.value, can_be_escaped=True)
            # except AS ${err}
            if self.try_assign(try_branch) is not None:
                error_var = try_branch.header.get_token(Token.VARIABLE)
                if error_var is not None:
                    self.handle_assign_variable(error_var, ignore_var_conversion=False)
                    for variable in self.variables[-1].values():
                        variable.current_scopy_only = True
            # visit body of branch
            for item in try_branch.body:
                self.visit(item)
            branch_variables.append(self.variables.pop())
            try_branch = try_branch.next
        for branch in branch_variables:
            for name, variable in branch.items():
                if variable.current_scopy_only:
                    if not variable.is_used:
                        self.report_arg_or_var_rule(self.unused_variable, variable.token, variable.name)
                elif name not in try_variables:
                    try_variables[name] = variable
                else:
                    try_variables[name].is_used = try_variables[name].is_used and variable.is_used
                    if not variable.is_used:
                        try_variables[name].token = variable.token
        self.add_variables_from_if_to_scope(try_variables)

    def visit_Group(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        self.generic_visit(node)

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        for token in node.get_tokens(Token.KEYWORD):  # argument can be used in the keyword name
            self.find_not_nested_variable(token.value, can_be_escaped=False)
        for token in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, can_be_escaped=True)
        for token in node.get_tokens(Token.ASSIGN):  # we first check args, then assign for used and then overwritten
            self.handle_assign_variable(token)

    def visit_Var(self, node) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg.value, can_be_escaped=True)
        variable = node.get_token(Token.VARIABLE)
        if variable and utils.is_var_scope_local(node):
            self.handle_assign_variable(variable)

    def visit_TemplateArguments(self, node) -> None:  # noqa: N802
        for argument in node.data_tokens:
            self.find_not_nested_variable(argument.value, can_be_escaped=False)

    def handle_assign_variable(self, token, ignore_var_conversion: bool = True) -> None:
        """
        Check if assign does not overwrite arguments or variables.

        Store assign variables for future overwriting checks.
        """
        value = token.value
        variable_match = search_variable(value, ignore_errors=True)
        name = variable_match.base
        if ignore_var_conversion:
            name = utils.remove_variable_type_conversion(name)
        normalized = utils.normalize_robot_name(name)
        if not normalized or name.startswith("_"):  # i.e. "${_}" -> "", or ${_ignore}
            return
        arg = self.arguments.get(normalized, None)
        if arg is not None:
            if not arg.is_used and self.branch_level == 0:
                self.report_arg_or_var_rule(self.argument_overwritten_before_usage, arg.token)
            arg.is_used = is_used = True
        else:
            is_used = False
        if not variable_match.items:  # not item assignment like ${var}[1] =
            variable_scope = self.variables[-1]
            if normalized in variable_scope:
                is_used = variable_scope[normalized].is_used
                if not is_used and not self.ignore_overwriting:
                    self.report_arg_or_var_rule(
                        self.variable_overwritten_before_usage,
                        variable_scope[normalized].token,
                        variable_scope[normalized].name,
                    )
            else:  # check for attribute access like .lower() or .x
                for variable_scope in self.variables[::-1]:
                    base_name = self.search_by_tokenize(normalized, variable_scope)
                    if base_name:
                        variable_scope[base_name[0]].is_used = True
                        self.variables[-1][normalized] = CachedVariable(variable_match.name, token, is_used=True)
                        return
        if self.in_loop:
            variable = CachedVariable(variable_match.name, token, is_used)
        else:
            variable = CachedVariable(variable_match.name, token, is_used=False)
        self.variables[-1][normalized] = variable

    def find_not_nested_variable(self, value: str, can_be_escaped: bool) -> None:
        r"""
        Find and process not nested variable.

        Examples:
            '${value}' -> value
            ${value_${nested}} -> nested
            'String with ${var} and $escaped' -> var, escaped

        Found variables are added to the scope.

        """
        identifiers = set("$@&%")
        n = len(value)
        i = 0
        full_match = False  # whether string is a variable only
        while True:
            # find the next '{'
            pos = value.find("{", i)
            if pos == -1:
                break
            # must be preceded by an identifier char
            if pos == 0 or value[pos - 1] not in identifiers:
                i = pos + 1
                continue
            # found an identifier + '{' opening
            start = pos + 1  # first char inside braces
            depth = 1
            j = start

            while j < n:
                # detect nested identifier + '{' (counts as increased nesting)
                if value[j] in identifiers and j + 1 < n and value[j + 1] == "{":
                    depth += 1
                    j += 2
                    continue

                if value[j] == "}":
                    depth -= 1
                    if depth == 0:
                        # call with the content inside the outermost braces
                        self.update_used_variables(value[start:j])
                        full_match = start == 2 and j == n - 1
                        i = j + 1
                        break
                j += 1
            else:
                # no matching closing brace found
                break
        # no need to search further if we matched fully ('${var}')
        if not can_be_escaped or full_match:
            return
        self.find_escaped_variables(value)

    def find_escaped_variables(self, value) -> None:
        """Find all $var escaped variables in the value string and process them."""
        # TODO: create iter_escaped_variables function
        if "$" not in value:
            return
        for match in self._ESCAPED_VAR_PATTERN.finditer(value):
            variable_name = match.group(1)
            if variable_name.isidentifier():
                self.update_used_variables(variable_name)

    def update_used_variables(self, variable_name) -> None:
        """
        Remove used variable from the arguments and variables store.

        If the normalized variable name was already defined, we need to remove it to know which variables are not used.
        If the variable is not found, we try to remove possible attribute access from the name and search again.
        For example:

          arg.attr -> arg
          arg["value"] -> arg
        """
        normalized = utils.normalize_robot_name(variable_name)
        if self.used_in_scope:
            self.used_in_scope[-1].add(normalized)
        for variable_scope in self.variable_namespaces():
            self._set_variable_as_used(normalized, variable_scope)

    def variable_namespaces(self):
        yield self.arguments
        yield self.section_variables
        yield from self.variables[::-1]

    def _set_variable_as_used(self, normalized_name: str, variable_scope: dict[str, CachedVariable]) -> None:
        """If variable is found in variable_scope, set it as used."""
        if normalized_name in variable_scope:
            variable_scope[normalized_name].is_used = True
        else:
            self.search_by_tokenize(normalized_name, variable_scope)

    def search_by_tokenize(self, variable_name, variable_scope) -> list[str]:
        """Search variables in string by tokenizing variable name using Python ast."""
        if not variable_scope:
            return []
        # there is no syntax like ${var * 2}
        if self._VARIABLE_NAME_PATTERN.fullmatch(variable_name):
            if variable_name in variable_scope:
                variable_scope[variable_name].is_used = True
                return [variable_name]
            return []
        found = []
        for name in utils.get_variables_from_string(variable_name):
            if name in variable_scope:
                variable_scope[name].is_used = True
                found.append(name)
        return found


class ExpressionsChecker(VisitorChecker):
    expression_can_be_simplified: ExpressionCanBeSimplifiedRule
    misplaced_negative_condition: MisplacedNegativeConditionRule

    QUOTE_CHARS = {"'", '"'}
    CONDITION_KEYWORDS = {
        "passexecutionif",
        "setvariableif",
        "shouldbetrue",
        "shouldnotbetrue",
        "skipif",
    }
    COMPARISON_SIGNS = {"==", "!="}
    EMPTY_COMPARISON = {
        "${true}",
        "${false}",
        "true",
        "false",
        "[]",
        "{}",
        "set()",
        "list()",
        "dict()",
        "0",
    }

    def visit_If(self, node) -> None:  # noqa: N802
        condition_token = node.header.get_token(Token.ARGUMENT)
        self.check_condition(node.header.type, condition_token, node.condition)
        self.generic_visit(node)

    visit_While = visit_If  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        normalized_name = utils.normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name not in self.CONDITION_KEYWORDS:
            return
        condition_token = node.get_token(Token.ARGUMENT)
        if not condition_token:
            return
        self.check_condition(node.keyword, condition_token, condition_token.value)
        if normalized_name == "setvariableif":
            arguments = node.get_tokens(Token.ARGUMENT)
            if len(arguments) < 4:
                return
            for condition_token in arguments[2::2]:
                self.check_condition(node.keyword, condition_token, condition_token.value)

    def check_condition(self, node_name, condition_token, condition) -> None:
        if not condition:
            return
        try:
            variables = list(VariableMatches(condition))
        except VariableError:  # for example ${variable which wasn't closed properly
            return
        position = condition_token.col_offset + 1
        for match in variables:
            position += len(match.before)
            self.check_for_misplaced_not(condition_token, node_name, match.before, match.match, match.after)
            self.check_for_complex_condition(
                condition_token,
                node_name,
                match.before,
                match.match,
                match.after,
                position,
            )

    def check_for_misplaced_not(self, condition_token, node_name, left_side, variable, right_side) -> None:
        """
        Check if the condition contains misplaced not.

        An example of misplaced condition would be 'not ${variable} is None'.
        """
        if not (left_side.endswith("not ") and right_side.startswith(" is ")):
            return
        right_tokens = right_side.split(" ")
        orig_right_side = " ".join(right_tokens[1:3])
        original_condition = f"not {variable} {orig_right_side}"
        proposed_condition = f"{variable} is not {right_tokens[2]}"
        self.report(
            self.misplaced_negative_condition,
            block_name=node_name,
            original_condition=original_condition,
            proposed_condition=proposed_condition,
            node=condition_token,
            col=condition_token.col_offset + 1,
            end_col=condition_token.end_col_offset + 1,
        )

    def check_for_complex_condition(
        self, condition_token, node_name, left_side, variable, right_side, position
    ) -> None:
        """Check if right side of the equation can be simplified."""
        if not right_side:
            return
        normalized = right_side.lower().lstrip()  # ' == ${TRUE}' -> '== ${true}'
        if len(normalized) < 3:
            if normalized == ")" and left_side.endswith("len("):
                self.report(
                    self.expression_can_be_simplified,
                    block_name=node_name,
                    node=condition_token,
                    col=position - len("len("),
                    end_col=position + len(variable) + 1,
                )
            return
        equation = normalized[:2]  # '=='
        compared_value = normalized[2:].lstrip()  # '${true}'
        if equation not in self.COMPARISON_SIGNS:
            return
        if compared_value in self.EMPTY_COMPARISON:
            self.report(
                self.expression_can_be_simplified,
                block_name=node_name,
                node=condition_token,
                col=position,
                end_col=position + len(variable) + len(right_side),
            )


class NonLocalVariableChecker(VisitorChecker):
    no_global_variable: variables.NoGlobalVariableRule
    no_suite_variable: variables.NoSuiteVariableRule
    no_test_variable: variables.NoTestVariableRule

    non_local_variable_keywords = {
        "setglobalvariable",
        "setsuitevariable",
        "settestvariable",
        "settaskvariable",
    }

    def visit_KeywordCall(self, node: KeywordCall):  # noqa: N802
        keyword_token = node.get_token(Token.KEYWORD)
        if not keyword_token:
            return

        keyword_name = utils.normalize_robot_name(keyword_token.value, remove_prefix="builtin.")
        if keyword_name not in self.non_local_variable_keywords:
            return

        if keyword_name == "setglobalvariable":
            self._report(self.no_global_variable, keyword_token)
            return

        if keyword_name == "setsuitevariable":
            self._report(self.no_suite_variable, keyword_token)
            return

        if keyword_name in ["settestvariable", "settaskvariable"]:
            self._report(self.no_test_variable, keyword_token)
            return

    def visit_Var(self, node):  # noqa: N802
        """Visit VAR syntax introduced in Robot Framework 7. Is ignored in Robot < 7"""
        if not node.scope:
            return

        scope = node.scope.upper()
        if scope == "LOCAL":
            return

        option_token = node.get_token(Token.OPTION)

        if scope == "GLOBAL":
            self._report(self.no_global_variable, option_token)
            return

        if scope in ["SUITE", "SUITES"]:
            self._report(self.no_suite_variable, option_token)
            return

        if scope in ["TEST", "TASK"]:
            self._report(self.no_test_variable, option_token)
            return

        # Unexpected scope, or variable-defined scope

    def _report(self, rule: Rule, node) -> None:
        self.report(
            rule,
            node=node,
            lineno=node.lineno,
            col=node.col_offset + 1,
            end_col=node.col_offset + len(node.value) + 1,
        )


class UndefinedArgumentDefaultChecker(VisitorChecker):
    undefined_argument_default: arguments.UndefinedArgumentDefaultRule
    undefined_argument_value: arguments.UndefinedArgumentValueRule
    # used by AssertionEngine library
    assertion_operators = {"==", "!=", "<", ">", "<=", ">=", "*=", "^=", "$=", "$"}

    def visit_Arguments(self, node: Arguments):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value
            arg_name, default_val = utils.split_argument_default_value(arg)

            if arg_name == arg:
                # has no default
                continue

            if default_val == "":
                self.report(
                    self.undefined_argument_default,
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.col_offset + len(token.value) + 1,
                    arg_name=arg_name,
                )

    def visit_KeywordCall(self, node: KeywordCall):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value

            if arg in self.assertion_operators:
                continue
            if "=" not in arg or arg.startswith("="):
                # Is a positional arg
                continue

            arg_name, default_val = arg.split("=", maxsplit=1)
            if arg_name.endswith("\\"):
                # `=` is escaped
                continue

            if default_val != "":
                # Has a value
                continue

            # Falsly triggers if a positional argument ends with `=`
            # The language server has the same behavior
            self.report(
                self.undefined_argument_value,
                node=token,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(token.value) + 1,
                arg_name=arg_name,
            )


class UnusedDiagnosticChecker(AfterRunChecker):
    unused_disabler: DisablerNotUsedRule

    def scan_file(self, source_file: SourceFile, **kwargs) -> list[Diagnostic]:
        disablers = kwargs["disablers"]
        super().scan_file(source_file, **kwargs)
        self.check_unused_disablers(disablers)
        return self.issues

    def check_unused_disablers(self, disablers: "DisablersFinder"):
        for rule, disabler in disablers.not_used_disablers:
            self.report(
                self.unused_disabler,
                rule_name=rule,
                lineno=disabler.start_line,
                end_lineno=disabler.start_line,
                col=disabler.directive_col_start,
                end_col=disabler.directive_col_end,
            )


class MissingVariableTypeChecker(VisitorChecker):
    """Checker for variables without type annotations (RF 7.3+)."""

    missing_section_variable_type: typing.MissingSectionVariableTypeRule
    missing_argument_type: typing.MissingArgumentTypeRule
    missing_for_loop_variable_type: typing.MissingForLoopVariableTypeRule

    @staticmethod
    def has_type_annotation(var_name: str) -> bool:
        """
        Check if variable has type annotation (contains ': ' followed by type).

        Returns:
            True if variable has type annotation

        """
        # Type conversion syntax: ${var: type} - note the space after colon
        # vs embedded pattern: ${var:pattern} - no space after colon
        return ": " in var_name

    @staticmethod
    def is_ignore_variable(var_name: str) -> bool:
        """
        Check if variable is an ignore variable like ${_} or ${_name}.

        Args:
            var_name: Variable name from search_variable().base

        Returns:
            True if variable should be ignored (starts with underscore)

        """
        # Strip variable markers like ${, @{, &{, %}
        name = var_name.lstrip("$@&%{").rstrip("}")
        # Remove type annotation if present
        name = utils.remove_variable_type_conversion(name)
        return name == "_" or name.startswith("_")

    def should_report_missing_type(self, var_name: str) -> bool:
        """
        Check if variable should be reported for missing type annotation.

        Args:
            var_name: Variable name from search_variable()

        Returns:
            True if variable is missing type annotation and should be reported

        """
        try:
            var_match = search_variable(var_name, ignore_errors=True)
            return (
                var_match.base
                and not self.has_type_annotation(var_match.base)
                and not self.is_ignore_variable(var_match.base)
            )
        except VariableError:
            return False

    def visit_Variable(self, node: Variable) -> None:  # noqa: N802
        """Check variables in *** Variables *** section."""
        if node.errors:
            return
        token = node.data_tokens[0]
        if self.should_report_missing_type(token.value):
            var_match = search_variable(token.value, ignore_errors=True)
            self.report(
                self.missing_section_variable_type,
                variable_name=var_match.match,
                node=node,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )

    def visit_Var(self, node: Var) -> None:  # noqa: N802
        """Check VAR statements."""
        if node.errors:
            return
        variable = node.get_token(Token.VARIABLE)
        if not variable:
            return
        if self.should_report_missing_type(variable.value):
            var_match = search_variable(variable.value, ignore_errors=True)
            self.report(
                self.missing_section_variable_type,
                variable_name=var_match.match,
                node=node,
                lineno=variable.lineno,
                col=variable.col_offset + 1,
                end_col=variable.end_col_offset + 1,
            )

    def visit_KeywordCall(self, node: KeywordCall) -> None:  # noqa: N802
        """Check assignment expressions (${var} = Keyword)."""
        # TODO: we already search for variable in unused var checker - we can combine
        for token in node.get_tokens(Token.ASSIGN):
            if self.should_report_missing_type(token.value):
                var_match = search_variable(token.value, ignore_errors=True)
                self.report(
                    self.missing_section_variable_type,
                    variable_name=var_match.match,
                    node=node,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )

    def visit_Arguments(self, node: Arguments) -> None:  # noqa: N802
        """Check keyword arguments ([Arguments])."""
        for arg in node.get_tokens(Token.ARGUMENT):
            # Handle default values: ${arg: type}=default
            arg_name, _ = utils.split_argument_default_value(arg.value)
            if self.should_report_missing_type(arg_name):
                var_match = search_variable(arg_name, ignore_errors=True)
                self.report(
                    self.missing_argument_type,
                    variable_name=var_match.match,
                    node=node,
                    lineno=arg.lineno,
                    col=arg.col_offset + 1,
                    end_col=arg.col_offset + len(arg_name) + 1,
                )

    def visit_For(self, node: For) -> None:  # noqa: N802
        """Check FOR loop variables."""
        if not node.header.errors:
            for variable in node.header.get_tokens(Token.VARIABLE):
                if self.should_report_missing_type(variable.value):
                    var_match = search_variable(variable.value, ignore_errors=True)
                    self.report(
                        self.missing_for_loop_variable_type,
                        variable_name=var_match.match,
                        node=node,
                        lineno=variable.lineno,
                        col=variable.col_offset + 1,
                        end_col=variable.end_col_offset + 1,
                    )
        self.generic_visit(node)  # Continue to nested loops
