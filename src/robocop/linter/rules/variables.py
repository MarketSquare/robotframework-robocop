from robocop.linter.rules import Rule, RuleParam, RuleSeverity


def comma_separated_list(value: str) -> list[str]:
    return value.split(",")


class EmptyVariableRule(Rule):
    r"""
    Variable without value.

    Variables with placeholder ${EMPTY} values are more explicit.

    Incorrect code example::

        *** Variables ***
        ${VAR_NO_VALUE}
        ${VAR_WITH_EMPTY}    ${EMPTY}
        @{MULTILINE_FIRST_EMPTY}
        ...
        ...    value
        ${EMPTY_WITH_BACKSLASH}  \

    Correct code::

        *** Keywords ***
        Create Variables
            VAR    @{var_no_value}
            VAR    ${var_with_empty}    ${EMPTY}

        Incorrect code example::

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

    """

    name = "empty-variable"
    rule_id = "VAR01"
    message = "Empty variable value"
    severity = RuleSeverity.INFO
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


class UnusedVariableRule(Rule):
    """
    Unused variable.

    Incorrect code example::

        *** Keywords ***
        Get Triangle Base Points
            [Arguments]       ${triangle}
            ${p1}    ${p2}    ${p3}    Get Triangle Points    ${triangle}
            Log      Triangle base points are: ${p1} and ${p2}.
            RETURN   ${p1}    ${p2}  # ${p3} is never used

    Use ``${_}`` variable name if you purposefully do not use variable::

        *** Keywords ***
        Process Value 10 Times
            [Arguments]    ${value}
            FOR    ${_}   IN RANGE    10
                Process Value    ${value}
            END

    Note that some keywords may use your local variables even if you don't pass them directly. For example
    BuiltIn ``Replace Variables`` or any custom keyword that retrieves variables from local scope. In such case
    Robocop will still raise ``unused-variable`` even if variable is used.

    """

    name = "unused-variable"
    rule_id = "VAR02"
    message = "Variable '{name}' is assigned but not used"
    severity = RuleSeverity.INFO
    added_in_version = "3.2.0"


class VariableOverwrittenBeforeUsageRule(Rule):
    """
    Local variable is overwritten before usage.

    Local variable in Keyword, Test Case or Task is overwritten before it is used::

        *** Keywords ***
        Overwritten Variable
            ${value}    Keyword
            ${value}    Keyword

    In case the value of the variable is not important, it is possible to use ``${_}`` name::

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


class NoGlobalVariableRule(Rule):
    """
    Global variable defined outside ``*** Variables ***`` section.

    Setting or updating global variables in a test/keyword often leads to hard-to-understand
    code. In most cases, you're better off using local variables.

    Changes in global variables during a test are hard to track because you must remember what's
    happening in multiple pieces of code at once. A line in a seemingly unrelated file can mess
    up your understanding of what the code should be doing.

    Local variables don't suffer from this issue because they are always created in the
    keyword/test you're looking at.

    In this example, the keyword changes the global variable. This will cause the test to fail.
    Looking at just the test, it's unclear why the test fails. It only becomes clear if you also
    remember the seemingly unrelated keyword::

        *** Variables ***
        ${hello}    Hello, world!

        *** Test Cases ***
        My Amazing Test
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Global Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax::

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
    remember the seemingly unrelated keyword::

        *** Test Cases ***
        My Amazing Test
            Set Suite Variable    ${hello}    Hello, world!
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Suite Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax::

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
    remember the seemingly unrelated keyword::

        *** Test Cases ***
        My Amazing Test
            Set Test Variable    ${hello}    Hello, world!
            Do A Thing
            Should Be Equal    ${hello}    Hello, world!

        *** Keywords ***
        Do A Thing
            Set Test Variable    ${hello}    Goodnight, moon!

    Using the VAR-syntax::

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


class NonLocalVariablesShouldBeUppercaseRule(Rule):
    """
    Non-local variable is not uppercase.

    Non-local variable is not uppercase to easily identify scope of the variable.

    Incorrect code example::

        *** Test Cases ***
        Test case
            Set Task Variable    ${my_var}           1
            Set Suite Variable   ${My Var}           1
            Set Test Variable    ${myvar}            1
            Set Global Variable  ${my_var${NESTED}}  1

    Correct code::

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


class PossibleVariableOverwritingRule(Rule):
    """
    Variable may overwrite similar variable inside code block.

    Variable names are case-insensitive, and also spaces and underscores are ignored.
    Following assignments overwrite the same variable::

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
    severity = RuleSeverity.INFO
    added_in_version = "1.10.0"


class HyphenInVariableNameRule(Rule):
    """
    Hyphen in the variable name.

    Hyphens can be treated as minus sign by Robot Framework. If it is not intended, avoid using hyphen (``-``)
    character in variable name.

    Incorrect code example::

        *** Test Cases ***
        Test case
            ${var2}  Set Variable  ${${var}-${var2}}

    That's why there is a possibility that hyphen in name is not recognized as part of the name but as a minus sign.
    Better to use underscore instead:

    Correct code::

        *** Test Cases ***
        Test case
            ${var2}  Set Variable  ${${var}_${var2}}

    Hyphens in ``*** Variables ***`` section or in ``[Arguments]`` are also reported for consistency reason.

    """

    name = "hyphen-in-variable-name"
    rule_id = "VAR09"
    message = "Hyphen in variable name '{variable_name}'"
    severity = RuleSeverity.INFO
    added_in_version = "1.10.0"


class InconsistentVariableNameRule(Rule):
    """
    Variable with inconsistent naming.

    Variable names are case-insensitive and ignore underscores and spaces. It is possible to
    write the variable in multiple ways, and it will be a valid Robot Framework code. However,
    it makes it harder to maintain the code that does not follow the consistent naming.

    Incorrect code example::

        *** Keywords ***
        Check If User Is Admin
            [Arguments]    ${username}
            ${role}    Get User Role     ${username}
            IF    '${ROLE}' == 'Admin'   # inconsistent name with ${role}
                Log    ${Username} is an admin  # inconsistent name with ${username}
            ELSE
                Log    ${user name} is not an admin  # inconsistent name
            END

    Correct code::

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


class OverwritingReservedVariableRule(Rule):
    """
    Variable overwrites reserved variable.

    Overwriting reserved variables may bring unexpected results.
    For example, overwriting variable with name ``${LOG_LEVEL}`` can break Robot Framework logging.
    See the full list of reserved variables at
    `Robot Framework User Guide <https://robotframework.org/robotframework/latest/RobotFrameworkUserGuide.html#automatic-variables>`_

    """

    name = "overwriting-reserved-variable"
    rule_id = "VAR11"
    message = "{var_or_arg} '{variable_name}' overwrites reserved variable '{reserved_variable}'"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"


class DuplicatedAssignedVarNameRule(Rule):
    """
    Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following variables
    are duplicates::

        *** Test Cases ***
        Test
            ${var}  ${VAR}  ${v_ar}  ${v ar}  Keyword

    It is possible to use `${_}` to note that variable name is not important and will not be used::

        *** Keywords ***
        Get Middle Element
            [Arguments]    ${list}
            ${_}    ${middle}    ${_}    Split List    ${list}
            RETURN    ${middle}

    """

    name = "duplicated-assigned-var-name"
    rule_id = "VAR12"
    message = "Assigned variable name '{variable_name}' is already used"
    severity = RuleSeverity.INFO
    added_in_version = "1.12.0"
