from __future__ import annotations

from typing import TYPE_CHECKING

from robot.api import Token

from robocop.linter import sonar_qube
from robocop.linter.fix import Fix, FixApplicability, FixAvailability, TextEdit
from robocop.linter.rules import FixableRule, Rule, RuleParam, RuleSeverity
from robocop.linter.utils import misc as utils
from robocop.version_handling import TYPE_SUPPORTED

if TYPE_CHECKING:
    from robot.parsing.model.statements import Node, Statement, Var, Variable
    from robot.variables.search import SearchResult

    from robocop.linter.diagnostics import Diagnostic

EMPTY_VALUE_SEPARATOR = "    "

RESERVED_VARIABLES = {
    "testname": "${TEST_NAME}",
    "testtags": "@{TEST_TAGS}",
    "testdocumentation": "${TEST_DOCUMENTATION}",
    "teststatus": "${TEST_STATUS}",
    "testmessage": "${TEST_MESSAGE}",
    "prevtestname": "${PREV_TEST_NAME}",
    "prevteststatus": "${PREV_TEST_STATUS}",
    "prevtestmessage": "${PREV_TEST_MESSAGE}",
    "suitename": "${SUITE_NAME}",
    "suitesource": "${SUITE_SOURCE}",
    "suitedocumentation": "${SUITE_DOCUMENTATION}",
    "suitemetadata": "&{SUITE_METADATA}",
    "suitestatus": "${SUITE_STATUS}",
    "suitemessage": "${SUITE_MESSAGE}",
    "keywordstatus": "${KEYWORD_STATUS}",
    "keywordmessage": "${KEYWORD_MESSAGE}",
    "loglevel": "${LOG_LEVEL}",
    "outputfile": "${OUTPUT_FILE}",
    "logfile": "${LOG_FILE}",
    "reportfile": "${REPORT_FILE}",
    "debugfile": "${DEBUG_FILE}",
    "outputdir": "${OUTPUT_DIR}",
    # "options": "&{OPTIONS}", This variable is widely used and is relatively safe to overwrite
}


def comma_separated_list(value: str) -> list[str]:
    return value.split(",")


def report_non_local_scope(rule: Rule, node: Node) -> None:
    """Report a variable scope rule on the token that defines the scope."""
    if not rule.enabled:
        return
    rule.report(
        node=node,
        lineno=node.lineno,
        col=node.col_offset + 1,
        end_col=node.col_offset + len(node.value) + 1,
    )


class EmptyVariableRule(FixableRule):
    r"""
    Variable without value.

    Variables with placeholder ${EMPTY} values are more explicit.

    Incorrect code example:

        *** Variables ***
        ${VAR_NO_VALUE}
        ${VAR_WITH_EMPTY}    ${EMPTY}
        @{MULTILINE_FIRST_EMPTY}
        ...
        ...    value
        ${EMPTY_WITH_BACKSLASH}  \

    Correct code:

        *** Keywords ***
        Create Variables
            VAR    @{var_no_value}
            VAR    ${var_with_empty}    ${EMPTY}

        Incorrect code example:

        *** Variables ***
        ${VAR_NO_VALUE}    ${EMPTY}
        ${VAR_WITH_EMPTY}    ${EMPTY}
        @{MULTILINE_FIRST_EMPTY}
        ...    ${EMPTY}
        ...    value
        ${EMPTY_WITH_BACKSLASH}  \


        *** Keywords ***
        Create Variables
            VAR    @{var_no_value}    @{EMPTY}
            VAR    ${var_with_empty}    ${EMPTY}

    You can configure ``empty-variable`` rule to run only in ```*** Variables ***``` section or on
    ``VAR`` statements using ``variable_source`` parameter.

    The fix adds the explicit empty value, using the variable type to select it: ``${EMPTY}`` for scalars,
    ``@{EMPTY}`` for lists and ``&{EMPTY}`` for dictionaries. Empty values in a list and the ``\`` values are
    always replaced with ``${EMPTY}``.

    """

    name = "empty-variable"
    rule_id = "VAR01"
    message = "Empty variable value"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="variable_source",
            default="section,var",
            converter=comma_separated_list,
            show_type="comma separated list",
            desc="Variable sources that will be checked",
        )
    ]
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.COMPLETE, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0912",)
    fix_availability = FixAvailability.ALWAYS

    def check_variable(self, node: Variable) -> None:
        """Check variable defined in the ``*** Variables ***`` section."""
        if not self.enabled or node.errors:
            return
        if not node.value:  # catch variable declaration without any value
            self.report(node=node, end_col=node.end_col_offset)
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(node=node, lineno=token.lineno, col=1, end_col=token.end_col_offset + 1)

    def check_var(self, node: Var) -> None:
        """Check variable defined with the ``VAR`` syntax."""
        if not self.enabled or node.errors:
            return
        if not node.value:  # catch variable declaration without any value
            first_data = node.data_tokens[0]
            self.report(
                node=node,
                col=first_data.col_offset + 1,
                end_col=first_data.end_col_offset + 1,
            )
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    node=node,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )

    @staticmethod
    def _find_empty_value(node: Statement, diag: Diagnostic) -> Token | None:
        """Find the empty argument token reported by the diagnostic using its end position."""
        return next(
            (
                token
                for token in node.get_tokens(Token.ARGUMENT)
                if (not token.value or token.value == "\\")
                and token.lineno == diag.range.start.line
                and token.end_col_offset + 1 == diag.range.end.character
            ),
            None,
        )

    def fix(self, diag: Diagnostic, source_lines: list[str]) -> Fix | None:  # noqa: ARG002
        """Replace the empty value with the explicit ``${EMPTY}`` variable."""
        node = diag.node
        if node is None:
            return None
        empty_value = self._find_empty_value(node, diag)
        if empty_value is not None:
            # empty values are zero-width tokens and require the separator, the backslash is replaced in place
            start_col = empty_value.col_offset + 1
            end_col = empty_value.end_col_offset + 1
            separator = "" if empty_value.value else EMPTY_VALUE_SEPARATOR
            replacement = f"{separator}${{EMPTY}}"
            message = "Replace the empty value with ${EMPTY}"
        else:
            name = node.get_token(Token.VARIABLE)
            if name is None or not name.value:
                return None
            start_col = end_col = name.end_col_offset + 1
            replacement = f"{EMPTY_VALUE_SEPARATOR}{name.value[0]}{{EMPTY}}"
            message = f"Add the explicit {name.value[0]}{{EMPTY}} value"
            empty_value = name
        edit = TextEdit(
            rule_id=self.rule_id,
            rule_name=self.name,
            start_line=empty_value.lineno,
            start_col=start_col,
            end_line=empty_value.lineno,
            end_col=end_col,
            replacement=replacement,
        )
        return Fix(edits=[edit], message=message, applicability=FixApplicability.SAFE)


class UnusedVariableRule(Rule):
    """
    Unused variable.

    Incorrect code example:

        *** Keywords ***
        Get Triangle Base Points
            [Arguments]       ${triangle}
            ${p1}    ${p2}    ${p3}    Get Triangle Points    ${triangle}
            Log      Triangle base points are: ${p1} and ${p2}.
            RETURN   ${p1}    ${p2}  # ${p3} is never used

    You can use ``${_}`` variable name or start variable name with ``_`` underscore if you purposefully do not
    use variable:

        *** Keywords ***
        Process Value 10 Times
            [Arguments]    ${value}
            FOR    ${_}   IN RANGE    10
                Process Value    ${value}
            END
            ${_first}    ${second}    Unpack List    @{LIST}

    Note that some keywords may use your local variables even if you don't pass them directly. For example,
    BuiltIn ``Replace Variables`` or any custom keyword that retrieves variables from a local scope. In this case,
    Robocop will still raise an ``unused-variable`` even if the variable is actually used.

    You can configure the rule to ignore specific variable names in the ``*** Variables ***`` section using
    the ``ignore`` parameter. This is useful for variables that are used by external listeners, libraries,
    or variable files:

        robocop check --configure unused-variable.ignore=suite_param,other_var

    Variable names are matched case-insensitively following Robot Framework conventions.

    """

    name = "unused-variable"
    rule_id = "VAR02"
    message = "Variable '{name}' is assigned but not used"
    severity = RuleSeverity.WARNING
    parameters = [
        RuleParam(
            name="ignore",
            default="",
            converter=str,
            show_type="comma separated list",
            desc="Comma-separated list of variable names to ignore in *** Variables *** section (case-insensitive)",
        )
    ]
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0920",)


class VariableOverwrittenBeforeUsageRule(Rule):
    """
    Local variable is overwritten before usage.

    Local variable in Keyword, Test Case or Task is overwritten before it is used:

        *** Keywords ***
        Overwritten Variable
            ${value}    Keyword
            ${value}    Keyword

    In case the value of the variable is not important, it is possible to use ``${_}`` name:

        *** Test Cases ***
        Call keyword and ignore some return values
            ${_}    ${item}    Unpack List    @{LIST}
            FOR    ${_}    IN RANGE  10
                Log    Run this code 10 times.
            END

    """

    name = "variable-overwritten-before-usage"
    rule_id = "VAR03"
    message = "Local variable '{name}' is overwritten before usage"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CLEAR, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0922",)


class NoGlobalVariableRule(Rule):
    """
    Global variable defined outside the ``*** Variables ***`` section.

    Setting or updating global variables in a test/keyword often leads to hard-to-understand
    code. In most cases, you're better off using local variables.

    Changes in global variables during a test are hard to track because you must remember what's
    happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
    up your understanding of what the code should be doing.

    Local variables don't suffer from this issue because they are always created in the
    keyword/test you're looking at.

    In this example, the keyword changes the global variable. This will cause the test to fail.
    Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
    remember the seemingly unrelated keyword:

        *** Variables ***
        ${hello}    Hello, world!

        *** Test Cases ***
        My Amazing Test
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Global Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax:

        *** Variables ***
        ${hello}    Hello, world!

        *** Test Cases ***
        My Amazing Test
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            VAR    ${hello}    Goodnight, moon!    scope=GLOBAL

    In some specific situations, global variables are a great tool. But most of the time, it
    makes code needlessly hard to understand.
    """

    name = "no-global-variable"
    rule_id = "VAR04"
    message = "Variable with global scope defined outside variables section"
    severity = RuleSeverity.WARNING
    added_in_version = "5.6.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0929",)

    def check(self, node: Node) -> None:
        report_non_local_scope(self, node)


class NoSuiteVariableRule(Rule):
    """
    Using suite variables in a test/keyword often leads to hard-to-understand code. In most
    cases, you're better off using local variables.

    Changes in suite variables during a test are hard to track because you must remember what's
    happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
    up your understanding of what the code should be doing.

    Local variables don't suffer from this issue because they are always created in the
    keyword/test you're looking at.

    In this example, the keyword changes the suite variable. This will cause the test to fail.
    Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
    remember the seemingly unrelated keyword:

        *** Test Cases ***
        My Amazing Test
            Set Suite Variable    ${hello}    Hello, world!
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Suite Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax:

        *** Test Cases ***
        My Amazing Test
            VAR    ${hello}    Hello, world!    scope=SUITE
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            VAR    ${hello}    Goodnight, moon!    scope=SUITE

    In some specific situations, suite variables are a great tool. But most of the time, it
    makes code needlessly hard to understand.
    """

    name = "no-suite-variable"
    rule_id = "VAR05"
    message = "Variable defined with suite scope"
    severity = RuleSeverity.WARNING
    added_in_version = "5.6.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0930",)

    def check(self, node: Node) -> None:
        report_non_local_scope(self, node)


class NoTestVariableRule(Rule):
    """
    Using test/task variables in a test/keyword often leads to hard-to-understand code. In most
    cases, you're better off using local variables.

    Changes in test/task variables during a test are hard to track because you must remember what's
    happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
    up your understanding of what the code should be doing.

    Local variables don't suffer from this issue because they are always created in the
    keyword/test you're looking at.

    In this example, the keyword changes the test/task variable. This will cause the test to fail.
    Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
    remember the seemingly unrelated keyword:

        *** Test Cases ***
        My Amazing Test
            Set Test Variable    ${hello}    Hello, world!
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Test Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax:

        *** Test Cases ***
        My Amazing Test
            VAR    ${hello}    Hello, world!    scope=TEST
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            VAR    ${hello}    Goodnight, moon!    scope=TEST

    In some specific situations, test/task variables are a great tool. But most of the time, it
    makes code needlessly hard to understand.
    """

    name = "no-test-variable"
    rule_id = "VAR06"
    message = "Variable defined with test/task scope"
    severity = RuleSeverity.WARNING
    added_in_version = "5.6.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0931",)

    def check(self, node: Node) -> None:
        report_non_local_scope(self, node)


class NonLocalVariablesShouldBeUppercaseRule(Rule):
    """
    Non-local variable is not uppercase.

    Non-local variable is not uppercase to easily identify scope of the variable.

    Incorrect code example:

        *** Test Cases ***
        Test case
            Set Task Variable    ${my_var}           1
            Set Suite Variable   ${My Var}           1
            Set Test Variable    ${myvar}            1
            Set Global Variable  ${my_var${NESTED}}  1

    Correct code:

        *** Test Cases ***
        Test case
            Set Task Variable    ${MY_VAR}           1
            Set Suite Variable   ${MY VAR}           1
            Set Test Variable    ${MY_VAR}           1
            Set Global Variable  ${MY VAR${nested}}  1

    """

    name = "non-local-variables-should-be-uppercase"
    rule_id = "VAR07"
    message = "Non local variable is not uppercase"
    severity = RuleSeverity.WARNING
    added_in_version = "1.4.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0310",)

    def check(self, variable_name: str, node: Node, token: Token) -> None:
        normalized_var_name = utils.remove_nested_variables(variable_name)
        if not normalized_var_name:
            return
        if TYPE_SUPPORTED:
            normalized_var_name, *_ = normalized_var_name.split(": ", 1)
        # a variable as a keyword argument can contain lowercase nested variable
        # because the actual value of it may be uppercase
        if normalized_var_name.isupper():
            return
        self.report(node=node, col=token.col_offset + 1, end_col=token.end_col_offset + 1)


class PossibleVariableOverwritingRule(Rule):
    """
    Variable may overwrite similar variable inside code block.

    Variable names are case-insensitive, and also spaces and underscores are ignored.
    Following assignments overwrite the same variable:

        *** Keywords ***
        Retrieve Usernames
            ${username}      Get Username       id=1
            ${User Name}     Get Username       id=2
            ${user_name}     Get Username       id=3

    Use consistent variable naming guidelines to avoid unintended variable overwriting.

    """

    name = "possible-variable-overwriting"
    rule_id = "VAR08"
    message = "Variable '{variable_name}' may overwrite similar variable inside '{block_name}' {block_type}"
    severity = RuleSeverity.WARNING
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0316",)


class HyphenInVariableNameRule(Rule):
    """
    Hyphen in the variable name.

    Hyphens can be treated as minus sign by Robot Framework. If it is not intended, avoid using hyphen (``-``)
    character in variable name.

    Incorrect code example:

        *** Test Cases ***
        Test case
            ${var2}  Set Variable  ${${var}-${var2}}

    That's why there is a possibility that hyphen in name is not recognized as part of the name but as a minus sign.
    Better to use underscore instead:

    Correct code:

        *** Test Cases ***
        Test case
            ${var2}  Set Variable  ${${var}_${var2}}

    Hyphens in ``*** Variables ***`` section or in ``[Arguments]`` are also reported for consistency reason.

    """

    name = "hyphen-in-variable-name"
    rule_id = "VAR09"
    message = "Hyphen in variable name '{variable_name}'"
    severity = RuleSeverity.WARNING
    added_in_version = "1.10.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0317",)

    def check(self, token: Token, name: str) -> None:
        if "-" not in name:
            return
        self.report(
            variable_name=token.value,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.end_col_offset + 1,
        )


class InconsistentVariableNameRule(Rule):
    """
    Variable with inconsistent naming.

    Variable names are case-insensitive and ignore underscores and spaces. It is possible to
    write the variable in multiple ways, and it will be a valid Robot Framework code. However,
    it makes it harder to maintain the code that does not follow the consistent naming.

    Incorrect code example:

        *** Keywords ***
        Check If User Is Admin
            [Arguments]    ${username}
            ${role}    Get User Role     ${username}
            IF    '${ROLE}' == 'Admin'   # inconsistent name with ${role}
                Log    ${Username} is an admin  # inconsistent name with ${username}
            ELSE
                Log    ${user name} is not an admin  # inconsistent name
            END

    Correct code:

        *** Keywords ***
        Check If User Is Admin
            [Arguments]    ${username}
            ${role}    Get User Role     ${username}
            IF    '${role}' == 'Admin'
                Log    ${username} is an admin
            ELSE
                Log    ${username} is not an admin
            END

    """

    name = "inconsistent-variable-name"
    rule_id = "VAR10"
    message = "Variable '{name}' has inconsistent naming. First used as '{first_use}'"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0323",)


class OverwritingReservedVariableRule(Rule):
    """
    Variable overwrites reserved variable.

    Overwriting reserved variables may bring unexpected results.
    For example, overwriting a variable with the name ``${LOG_LEVEL}`` can break Robot Framework logging.
    See the full list of reserved variables at
    [Robot Framework User Guide](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables).

    """

    name = "overwriting-reserved-variable"
    rule_id = "VAR11"
    message = "{var_or_arg} '{variable_name}' overwrites reserved variable '{reserved_variable}'"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.CONVENTIONAL, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0324",)

    def check(self, token: Token, variable_match: SearchResult, name: str, var_or_arg: str) -> None:
        if variable_match.items:  # item assignments ${dict}[key] =
            return
        reserved_variable = RESERVED_VARIABLES.get(utils.normalize_robot_name(name))
        if reserved_variable is None:
            return
        self.report(
            var_or_arg=var_or_arg,
            variable_name=variable_match.match,
            reserved_variable=reserved_variable,
            node=token,
            lineno=token.lineno,
            col=token.col_offset + 1,
            end_col=token.col_offset + len(variable_match.match) + 1,
        )


class DuplicatedAssignedVarNameRule(Rule):
    """
    Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following variables
    are duplicates:

        *** Test Cases ***
        Test
            ${var}  ${VAR}  ${v_ar}  ${v ar}  Keyword

    It is possible to use `${_}` to note that variable name is not important and will not be used:

        *** Keywords ***
        Get Middle Element
            [Arguments]    ${list}
            ${_}    ${middle}    ${_}    Split List    ${list}
            RETURN    ${middle}

    """

    name = "duplicated-assigned-var-name"
    rule_id = "VAR12"
    message = "Assigned variable name '{variable_name}' is already used"
    severity = RuleSeverity.WARNING
    added_in_version = "1.12.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.DISTINCT, issue_type=sonar_qube.SonarQubeIssueType.CODE_SMELL
    )
    deprecated_names = ("0812",)


class AutomaticVariableNotAvailableRule(Rule):
    """
    Automatic variable used in a context where Robot Framework does not provide it.

    Robot Framework has several automatic variables whose availability is limited to a specific execution context:

    - ``${TEST NAME}``, ``@{TEST TAGS}``, and ``${TEST DOCUMENTATION}`` are available while a test is running.
    - ``${TEST STATUS}`` and ``${TEST MESSAGE}`` are available only in a test teardown.
    - ``${SUITE STATUS}`` and ``${SUITE MESSAGE}`` are available only in a suite teardown.
    - ``${KEYWORD STATUS}`` and ``${KEYWORD MESSAGE}`` are available only in a user keyword teardown.

    Using one of these variables directly in another context fails at runtime:

        *** Test Cases ***
        Invalid automatic variables
            Log    ${KEYWORD STATUS}
            Log    ${TEST STATUS}
            [Teardown]    Log    ${SUITE STATUS}

    Use each variable in the context where Robot Framework makes it available:

        *** Settings ***
        Suite Teardown    Log    ${SUITE STATUS}
        Test Teardown     Log    ${TEST STATUS}

        *** Test Cases ***
        Valid automatic variables
            Log    ${TEST NAME}

        *** Keywords ***
        Keyword with teardown
            No Operation
            [Teardown]    Log    ${KEYWORD STATUS}

    Robocop deliberately does not report these variables inside user keyword definitions. A user keyword can be called
    from a test, test teardown, suite teardown, or another user keyword teardown, so its actual execution context cannot
    be determined reliably from the file where it is defined. For example, ``${TEST NAME}`` in a user keyword can be
    valid when called by a test but invalid when called by a suite setup. This conservative behavior avoids presenting
    call-context guesses as certain errors.

    See the official
    [automatic variable scope table](https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables).
    The rule has no automatic fix because choosing a replacement or moving code requires understanding its intent.

    """

    name = "automatic-variable-not-available"
    rule_id = "VAR13"
    message = "Automatic variable '{variable}' is not available in {context}; it is only available in {available_in}"
    severity = RuleSeverity.WARNING
    added_in_version = "9.0.0"
    sonar_qube_attrs = sonar_qube.SonarQubeAttributes(
        clean_code=sonar_qube.CleanCodeAttribute.LOGICAL, issue_type=sonar_qube.SonarQubeIssueType.BUG
    )

    scopes = {
        "testname": ("test case", frozenset({"test setup", "test case body", "test teardown"})),
        "testtags": ("test case", frozenset({"test setup", "test case body", "test teardown"})),
        "testdocumentation": ("test case", frozenset({"test setup", "test case body", "test teardown"})),
        "teststatus": ("test teardown", frozenset({"test teardown"})),
        "testmessage": ("test teardown", frozenset({"test teardown"})),
        "suitestatus": ("suite teardown", frozenset({"suite teardown"})),
        "suitemessage": ("suite teardown", frozenset({"suite teardown"})),
        "keywordstatus": ("user keyword teardown", frozenset({"user keyword teardown"})),
        "keywordmessage": ("user keyword teardown", frozenset({"user keyword teardown"})),
    }

    def check(self, token: Token, variable: str, normalized_name: str, context: str, offset: int) -> None:
        scope = self.scopes.get(normalized_name)
        if scope is None:
            return
        available_in, valid_contexts = scope
        if context in valid_contexts:
            return
        col = token.col_offset + offset + 1
        self.report(
            variable=variable,
            context=context,
            available_in=available_in,
            node=token,
            lineno=token.lineno,
            col=col,
            end_col=col + len(variable),
        )
