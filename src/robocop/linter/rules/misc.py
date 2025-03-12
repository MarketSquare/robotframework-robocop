"""Miscellaneous checkers"""

import ast
from dataclasses import dataclass
from pathlib import Path

from robot.api import Token
from robot.errors import VariableError
from robot.parsing.model.blocks import TestCaseSection
from robot.parsing.model.statements import Arguments, KeywordCall, Teardown
from robot.utils import unescape
from robot.variables.search import search_variable

try:
    from robot.api.parsing import Comment, EmptyLine, If, Variable
except ImportError:
    from robot.parsing.model.statements import Comment, EmptyLine, Variable
try:
    from robot.api.parsing import Break, Continue, InlineIfHeader
except ImportError:
    InlineIfHeader, Break, Continue = None, None, None

from robocop.linter.rules import (
    Rule,
    RuleParam,
    RuleSeverity,
    SeverityThreshold,
    VisitorChecker,
    arguments,
    deprecated,
    variables,
)
from robocop.linter.utils import (  # FIXME: import as module
    ROBOT_VERSION,
    AssignmentTypeDetector,
    get_errors,
    keyword_col,
    normalize_robot_name,
    normalize_robot_var_name,
    parse_assignment_sign_type,
)
from robocop.linter.utils.misc import (
    RETURN_CLASSES,
    _is_var_scope_local,
    find_escaped_variables,
    get_variables_from_string,
)
from robocop.linter.utils.variable_matcher import VariableMatches


class KeywordAfterReturnRule(Rule):
    """
    Keyword call after ``[Return]`` setting.

    To improve readability use ``[Return]`` setting at the end of the keyword. If you want to return immediately
    from the keyword, use ``RETURN`` statement instead. ``[Return]`` does not return from the keyword but only
    sets the values that will be returned at the end of the keyword.

    Incorrect code example::

        *** Keywords ***
        Keyword
            Step
            [Return]    ${variable}
            ${variable}    Other Step

    Correct code::

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


class EmptyReturnRule(Rule):
    """
    ``[Return]`` is empty.

    ``[Return]`` statement is used to define variables returned from keyword. If you don't return anything from
    keyword,  don't use ``[Return]``.

    Incorrect code example::

        *** Keywords ***
        Keyword
            Gather Results
            Assert Results
            [Return]

    Correct code::

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


class NestedForLoopRule(Rule):
    """
    Not supported nested for loop.

    Older versions of Robot Framework did not support nested for loops::

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


class InconsistentAssignmentRule(Rule):
    """
    Not consistent assignment sign in the file.

    Use only one type of assignment sign in a file.

    Incorrect code example::

        *** Keywords ***
        Keyword
            ${var} =  Other Keyword
            No Operation

        Keyword 2
            No Operation
            ${var}  ${var2}    Some Keyword

    Correct code::

        *** Keywords ***
        Keyword
            ${var}    Other Keyword
            No Operation

        Keyword 2
            No Operation
            ${var}  ${var2}    Some Keyword

    By default, Robocop looks for most popular assignment sign in the file. It is possible to define expected
    assignment sign by running:

    .. tab-set::

        .. tab-item:: Cli

            .. code:: shell

                robocop check --configure inconsistent-assignment.assignment_sign_type=none

        .. tab-item:: Configuration file

            .. code:: toml

                [robocop.lint]
                configure = [
                    "inconsistent-assignment.assignment_sign_type=none"
                ]

    You can choose between following assignment signs:

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
            converter=parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
    ]
    added_in_version = "1.7.0"


class InconsistentAssignmentInVariablesRule(Rule):
    """
    Not consistent assignment sign in the ``*** Variables ***`` section.

    Use one type of assignment sign in Variables section.

    Incorrect code example::

        *** Variables ***
        ${var} =    1
        ${var2}=    2
        ${var3} =   3
        ${var4}     a
        ${var5}     b

    Correct code::

        *** Variables ***
        ${var}      1
        ${var2}     2
        ${var3}     3
        ${var4}     a
        ${var5}     b

    By default, Robocop looks for the most popular assignment sign in the file. It is possible to define expected
    assignment sign by running::

        robocop check --configure inconsistent-assignment-in-variables.assignment_sign_type=equal_sign

    You can choose between following signs:

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
            converter=parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        )
    ]
    added_in_version = "1.7.0"


class CanBeResourceFileRule(Rule):
    """
    No tests in the file, consider renaming file extension to ``.resource``.

    If the Robot file contains only keywords or variables, it's a good practice to use ``.resource`` extension.
    """

    name = "can-be-resource-file"
    rule_id = "MISC06"
    message = "No tests in '{file_name}' file, consider renaming to '{file_name_stem}.resource'"
    severity = RuleSeverity.INFO
    file_wide_rule = True
    added_in_version = "1.10.0"


class IfCanBeMergedRule(Rule):
    """
    IF statement can be merged with previous IF.

    ``IF`` statement follows another ``IF`` with identical conditions. It can be possibly merged into one.

    Example of rule violation::

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

    Similar but not identical ``IF``::

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


class InlineIfCanBeUsedRule(Rule):
    """
    IF can be replaced with inline IF.

    Short and simple ``IF`` statements can be replaced with ``inline IF``.

    Following ``IF``::

        IF    $condition
            BREAK
        END

    can be replaced with::

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


class UnreachableCodeRule(Rule):
    """
    Unreachable code.

    Detects the unreachable code after ``RETURN``, ``BREAK`` or ``CONTINUE`` statements.

    For example::

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


class MultilineInlineIfRule(Rule):
    """
    Multi-line inline IF.

    It's allowed to create ``inline IF`` that spans multiple lines, but it should be avoided,
    since it decreases readability. Try to use normal ``IF``/``ELSE`` instead.

    Incorrect code example::

        *** Keywords ***
        Keyword
            IF  ${condition}  Log  hello
            ...    ELSE       Log  hi!

    Correct code::

        *** Keywords ***
        Keyword
            IF  ${condition}    Log  hello     ELSE    Log  hi!

    or IF block can be used::

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


class UnnecessaryStringConversionRule(Rule):
    """
    # TODO: Not used atm, see if it was deprecated before
    Variable in condition has unnecessary string conversion.

    Expressions in Robot Framework are evaluated using Python's eval function. When a variable is used
    in the expression using the normal ``${variable}`` syntax, its value is replaced before the expression
    is evaluated. For example, with the following expression::

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

    "${filename}" will be replaced by "schema.avsc"::

        IF    schema.avsc == 'default'

    "schema.avsc" will not be recognized as Python variable. That's why you need to quote it::

        IF    '${filename}' == 'default'

    However it introduces unnecessary string conversion and can mask difference in the type. For example::

        ${numerical}    Set Variable    10  # ${numerical} is actually string 10, not integer 10
        IF    "${numerical}" == "10"

    You can use  ``$variable`` syntax instead::

        IF    $numerical == 10

    It will put the actual variable in the evaluated expression without converting it to string.

    """

    name = "unnecessary-string-conversion"
    rule_id = "MISC12"
    message = "Variable '{name}' in '{block_name}' condition has unnecessary string conversion"
    severity = RuleSeverity.INFO
    version = ">=4.0"
    added_in_version = "4.0.0"


class ExpressionCanBeSimplifiedRule(Rule):
    """
    Condition can be simplified.

    Evaluated expression can be simplified.

    Incorrect code example::

        *** Keywords ***
        Click On Element
            [Arguments]    ${locator}
            IF    ${is_element_visible}==${TRUE}    RETURN
            ${is_element_enabled}    Set Variable    ${TRUE}
            WHILE    ${is_element_enabled} != ${TRUE}
                ${is_element_enabled}    Get Element Status    ${locator}
            END
            Click    ${locator}

    Correct code::

        *** Keywords ***
        Click On Element
            [Arguments]    ${locator}
            IF    ${is_element_visible}    RETURN
            ${is_element_enabled}    Set Variable    ${FALSE}
            WHILE    not ${is_element_enabled}
                ${is_element_enabled}    Get Element Status    ${locator}
            END
            Click    ${locator}

    Comparisons to empty sequences (lists, dicts, sets), empty string or ``0`` can be also simplified::

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


class MisplacedNegativeConditionRule(Rule):
    """
    Position of not operator can be changed for better readability.

    Incorrect code example::

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

    Correct code::

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
            if isinstance(child, RETURN_CLASSES.return_setting_class):
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
                elif normalize_robot_name(child.keyword, remove_prefix="builtin.") == "returnfromkeyword":
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
            if isinstance(child, (RETURN_CLASSES.return_class, Break, Continue)):
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
                    end_col=child.end_col_offset + 1,
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
                    self.nested_for_loop, node=child, col=token.col_offset + 1, end_col=token.end_col_offset + 1
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
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.run_keyword_variants:
            col = keyword_col(node)
            self.report(
                self.if_can_be_used, run_keyword=node.keyword, node=node, col=col, end_col=col + len(node.keyword)
            )


class ConsistentAssignmentSignChecker(VisitorChecker):
    """
    Checker for inconsistent assignment signs.

    By default, this checker will try to autodetect most common assignment sign (separately for ``*** Variables ***``
    section and ``*** Test Cases ***``, ``*** Keywords ***`` sections) and report any inconsistent type of sign in
    particular file.

    To force one type of sign type you can configure two rules::

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

    def __init__(self):
        self.keyword_expected_sign_type = None
        self.variables_expected_sign_type = None
        super().__init__()

    def visit_File(self, node) -> None:  # noqa: N802
        self.keyword_expected_sign_type = self.inconsistent_assignment.assignment_sign_type
        self.variables_expected_sign_type = self.inconsistent_assignment_in_variables.assignment_sign_type
        if "autodetect" in [self.keyword_expected_sign_type, self.variables_expected_sign_type]:
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
            if not isinstance(child, Variable) or get_errors(child):
                continue
            var_token = child.get_token(Token.VARIABLE)
            self.check_assign_type(
                var_token, self.variables_expected_sign_type, self.inconsistent_assignment_in_variables
            )
        return node

    def check_assign_type(self, token, expected, issue_name) -> None:
        sign = AssignmentTypeDetector.get_assignment_sign(token.value)
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
        auto_detector = AssignmentTypeDetector()
        auto_detector.visit(node)
        return auto_detector


class EmptyVariableChecker(VisitorChecker):
    """Checker for variables without value."""

    empty_variable: variables.EmptyVariableRule

    def __init__(self):
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
        if get_errors(node):
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
        source = node.source if node.source else self.source
        if source:
            extension = Path(source).suffix
            file_name = Path(source).stem
            if (
                ".resource" not in extension
                and "__init__" not in file_name
                and node.sections
                and not any(isinstance(section, TestCaseSection) for section in node.sections)
            ):
                self.report(self.can_be_resource_file, file_name=Path(source).name, file_name_stem=file_name, node=node)


class IfChecker(VisitorChecker):
    """Checker for IF blocks"""

    if_can_be_merged: IfCanBeMergedRule
    inline_if_can_be_used: InlineIfCanBeUsedRule
    multiline_inline_if: MultilineInlineIfRule

    def visit_TestCase(self, node) -> None:  # noqa: N802
        if get_errors(node):
            return
        self.check_adjacent_ifs(node)

    visit_For = visit_If = visit_Keyword = visit_TestCase  # noqa: N815  # TODO: While, Try Except?

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
        for var1, var2 in zip(assign_1, assign_2):
            if self.normalize_var_name(var1) != self.normalize_var_name(var2):
                return False
        return True

    @staticmethod
    def tokens_length(tokens):
        return sum(len(token.value) for token in tokens)

    def check_whether_if_should_be_inline(self, node) -> None:
        if ROBOT_VERSION.major < 5:
            return
        if self.is_inline_if(node):
            if node.lineno != node.end_lineno:
                if_header = node.header.data_tokens[0]
                self.report(
                    self.multiline_inline_if,
                    node=node,
                    col=if_header.col_offset + 1,
                    end_lineno=node.end_lineno,
                    end_col=node.end_col_offset + 1,
                )
            return
        if (
            len(node.body) != 1
            or node.orelse  # TODO: it could still report with orelse? if short enough
            # IF with one branch and assign require ELSE to be valid, better to ignore it
            or getattr(node.body[0], "assign", None)
            or not isinstance(node.body[0], (KeywordCall, RETURN_CLASSES.return_class, Break, Continue))  # type: ignore[arg-type]
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
    for_keyword = {"continueforloop", "continueforloopif", "exitforloop", "exitforloopif"}

    def __init__(self):
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
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.for_keyword:
            col = keyword_col(node)
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


class SectionVariablesCollector(ast.NodeVisitor):
    """Visitor for collecting all variables in the suite"""

    def __init__(self):
        self.section_variables: dict[str, CachedVariable] = {}

    def visit_Variable(self, node) -> None:  # noqa: N802
        if get_errors(node):
            return
        var_token = node.get_token(Token.VARIABLE)
        variable_match = search_variable(var_token.value, ignore_errors=True)
        normalized = normalize_robot_name(variable_match.base)
        self.section_variables[normalized] = CachedVariable(variable_match.name, var_token, is_used=False)


class UnusedVariablesChecker(VisitorChecker):
    unused_argument: arguments.UnusedArgumentRule
    unused_variable: variables.UnusedVariableRule
    argument_overwritten_before_usage: arguments.ArgumentOverwrittenBeforeUsageRule
    variable_overwritten_before_usage: variables.VariableOverwrittenBeforeUsageRule

    def __init__(self):
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
        self.check_unused_variables_in_scope(self.section_variables)

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
        if get_errors(node):
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            if arg.value[0] in ("@", "&"):  # ignore *args and &kwargs
                continue
            if "=" in arg.value:
                arg_name, default_value = arg.value.split("=", maxsplit=1)
                self.find_not_nested_variable(default_value, is_var=False)
            else:
                arg_name = arg.value
            normalized_name = normalize_robot_var_name(arg_name)
            self.add_argument(arg_name, normalized_name, token=arg)

    def parse_embedded_arguments(self, name_token) -> None:
        """Store embedded arguments from keyword name. Ignore embedded variables patterns (${var:pattern})."""
        try:
            for token in name_token.tokenize_variables():
                if token.type == Token.VARIABLE:
                    normalized_name = normalize_robot_var_name(token.value)
                    name, *_ = normalized_name.split(":", maxsplit=1)
                    self.add_argument(token.value, name, token=token)
        except VariableError:
            pass

    def visit_If(self, node):  # noqa: N802
        if node.header.errors:
            return
        self.branch_level += 1
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, is_var=False)
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
            self.find_not_nested_variable(token.value, is_var=False)
        self.variables.append({})
        for child in node.body:
            self.visit(child)
        self.current_if_variables.append(self.variables.pop())
        if node.orelse:
            self.visit_IfBranch(node.orelse)

    def add_variables_from_if_to_scope(self, if_variables: dict[str, CachedVariable]) -> None:
        """
        Add all variables in given IF branch to common scope. If variable is used already in the branch, if it will
        also be mark as used.
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
            self.find_not_nested_variable(token.value, is_var=False)

    visit_TestTags = visit_ForceTags = visit_Metadata = visit_DefaultTags = visit_Variable = visit_ReturnStatement = (  # noqa: N815
        visit_ReturnSetting  # noqa: N815
    ) = visit_Teardown = visit_Timeout = visit_Return = visit_SuiteSetup = visit_SuiteTeardown = visit_TestSetup = (  # noqa: N815
        visit_TestTeardown  # noqa: N815
    ) = visit_Setup = visit_ResourceImport = visit_VariablesImport = visit_Tags = visit_Documentation = (  # noqa: N815
        visit_LibraryImport
    )

    def clear_variables_after_loop(self) -> None:
        """Remove used variables after loop finishes."""
        for index, scope in enumerate(self.variables):
            self.variables[index] = {name: variable for name, variable in scope.items() if not variable.is_used}

    def revisit_variables_used_in_loop(self) -> None:
        """
        Due to recursive nature of the loops, we need to revisit variables used in the loop again in case
        variable defined in the further part of the loop was used.

        In case of nested FOR/WHILE loops we're storing variables in separate stacks, that are merged until we reach
        outer END.

        For example::

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
            self.find_not_nested_variable(token.value, is_var=False)
        if node.limit:
            self.find_not_nested_variable(node.limit, is_var=False)
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
            self.find_not_nested_variable(token.value, is_var=False)
        for token in node.header.get_tokens(Token.VARIABLE):
            self.handle_assign_variable(token)
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
        for token in node.header.get_tokens(Token.ARGUMENT, Token.OPTION):
            self.find_not_nested_variable(token.value, is_var=False)
        self.variables.append({})
        if self.try_assign(node) is not None:
            error_var = node.header.get_token(Token.VARIABLE)
            if error_var is not None:
                self.handle_assign_variable(error_var)
        for item in node.body:
            self.visit(item)
        self.variables.pop()
        if node.next:
            self.visit_Try(node.next)

    def visit_Group(self, node):  # noqa: N802
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, is_var=False)
        self.generic_visit(node)

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT, Token.KEYWORD):  # argument can be used in keyword name
            self.find_not_nested_variable(token.value, is_var=False)
        for token in node.get_tokens(Token.ASSIGN):  # we first check args, then assign for used and then overwritten
            self.handle_assign_variable(token)

    def visit_Var(self, node) -> None:  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg.value, is_var=False)
        variable = node.get_token(Token.VARIABLE)
        if variable and _is_var_scope_local(node):
            self.handle_assign_variable(variable)

    def visit_TemplateArguments(self, node) -> None:  # noqa: N802
        for argument in node.data_tokens:
            self.find_not_nested_variable(argument.value, is_var=False)

    def handle_assign_variable(self, token) -> None:
        """
        Check if assign does not overwrite arguments or variables.

        Store assign variables for future overwriting checks.
        """
        value = token.value
        variable_match = search_variable(value, ignore_errors=True)
        normalized = normalize_robot_name(variable_match.base)
        if not normalized:  # ie. "${_}" -> ""
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
                if not variable_scope[normalized].is_used and not self.ignore_overwriting:
                    self.report_arg_or_var_rule(
                        self.variable_overwritten_before_usage, variable_scope[normalized].token, variable_match.name
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

    def find_not_nested_variable(self, value, is_var) -> None:
        r"""
        Find and process not nested variable.

        Search `value` string until there is ${variable} without other variables inside. Unescaped escaped syntax
        ($var or \\${var}). If variable does exist in assign variables or arguments, it is removed to denote it was
        used.
        """
        try:
            variables = list(VariableMatches(value))
        except VariableError:  # for example ${variable which wasn't closed properly
            return
        if not variables:
            if is_var:
                self.update_used_variables(value)
            elif "$" in value:
                self.find_escaped_variables(value)  # $var
                if r"\${" in value:  # \\${var}
                    unescaped = unescape(value)
                    self.find_not_nested_variable(unescaped, is_var=False)
            return
        replaced, after = "", ""
        for match in variables:
            replaced += f"{match.before}placeholder{match.after}"
            if match.before and "$" not in match.before and is_var:  # ${test.kws[0].msgs[${index}]}
                self.update_used_variables(match.before)
            # handle ${variable}[item][${syntax}]
            if match.base and match.base.startswith("{") and match.base.endswith("}"):  # inline val
                self.find_not_nested_variable(match.base[1:-1].strip(), is_var=False)
            else:
                self.find_not_nested_variable(match.base, is_var=True)
            for item in match.items:
                self.find_not_nested_variable(item, is_var=False)
            after = match.after
        self.find_escaped_variables(replaced)
        if after and "$" not in after and is_var:  # ${test.kws[0].msgs[${index}]}
            self.update_used_variables(after)

    def find_escaped_variables(self, value) -> None:
        """Find all $var escaped variables in the value string and process them."""
        for var in find_escaped_variables(value):
            self.update_used_variables(var)

    def update_used_variables(self, variable_name) -> None:
        """
        Remove used variable from the arguments and variables store.

        If the normalized variable name was already defined, we need to remove it to know which variables are not used.
        If the variable is not found, we try to remove possible attribute access from the name and search again.
        For example:

          arg.attr -> arg
          arg["value"] -> arg
        """
        normalized = normalize_robot_name(variable_name)
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

    @staticmethod
    def search_by_tokenize(variable_name, variable_scope) -> list[str]:
        """Search variables in string by tokenizing variable name using Python ast."""
        if not variable_scope:
            return []
        found = []
        for name in get_variables_from_string(variable_name):
            if name in variable_scope:
                variable_scope[name].is_used = True
                found.append(name)
        return found


class ExpressionsChecker(VisitorChecker):
    expression_can_be_simplified: ExpressionCanBeSimplifiedRule
    misplaced_negative_condition: MisplacedNegativeConditionRule

    QUOTE_CHARS = {"'", '"'}
    CONDITION_KEYWORDS = {"passexecutionif", "setvariableif", "shouldbetrue", "shouldnotbetrue", "skipif"}
    COMPARISON_SIGNS = {"==", "!="}
    EMPTY_COMPARISON = {"${true}", "${false}", "true", "false", "[]", "{}", "set()", "list()", "dict()", "0"}

    def visit_If(self, node) -> None:  # noqa: N802
        condition_token = node.header.get_token(Token.ARGUMENT)
        self.check_condition(node.header.type, condition_token, node.condition)
        self.generic_visit(node)

    visit_While = visit_If  # noqa: N815

    def visit_KeywordCall(self, node) -> None:  # noqa: N802
        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
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
                condition_token, node_name, match.before, match.match, match.after, position
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

        keyword_name = normalize_robot_name(keyword_token.value, remove_prefix="builtin.")
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

    def visit_Arguments(self, node: Arguments):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value

            # From the Robot User Guide:
            # "The syntax for default values is space sensitive. Spaces before
            # the `=` sign are not allowed."
            if "}=" not in arg:
                # has no default
                continue

            arg_name, default_val = arg.split("}=", maxsplit=1)

            if default_val == "":
                self.report(
                    self.undefined_argument_default,
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.col_offset + len(token.value) + 1,
                    arg_name=arg_name + "}",
                )

    def visit_KeywordCall(self, node: KeywordCall):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT):
            arg = token.value

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
