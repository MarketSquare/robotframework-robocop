"""Miscellaneous checkers"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from robot.api import Token
from robot.errors import VariableError
from robot.libraries import STDLIBS
from robot.parsing.model.blocks import Keyword, TestCase, TestCaseSection
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

from robocop.checkers import VisitorChecker
from robocop.rules import DefaultRule, RuleParam, RuleSeverity, SeverityThreshold
from robocop.utils import (
    ROBOT_VERSION,
    AssignmentTypeDetector,
    get_errors,
    keyword_col,
    normalize_robot_name,
    normalize_robot_var_name,
    parse_assignment_sign_type,
    token_col,
)
from robocop.utils.misc import (
    RETURN_CLASSES,
    _is_var_scope_local,
    find_escaped_variables,
    parse_keyword_order_param,
    parse_test_case_order_param,
)
from robocop.utils.variable_matcher import VariableMatches

RULE_CATEGORY_ID = "09"


def comma_separated_list(value: str) -> list[str]:
    return value.split(",")


rules = {
    "0901": DefaultRule(
        rule_id="0901",
        name="keyword-after-return",
        msg="{{ error_msg }}",
        severity=RuleSeverity.WARNING,
        docs="""
        To improve readability use ``[Return]`` setting at the end of the keyword. If you want to return immediately
        from the keyword, use ``RETURN`` statement instead. ``[Return]`` does not return from the keyword but only
        sets the values that will be returned at the end of the keyword.

        Bad::

            Keyword
                Step
                [Return]    ${variable}
                ${variable}    Other Step

        Good::

            Keyword
                Step
                ${variable}    Other Step
                [Return]    ${variable}

        """,
        added_in_version="1.0.0",
    ),
    "0903": DefaultRule(
        rule_id="0903",
        name="empty-return",
        msg="[Return] is empty",
        severity=RuleSeverity.WARNING,
        docs="""
        ``[Return]`` statement is used to define variables returned from keyword. If you don't return anything from
        keyword,  don't use ``[Return]``.
        """,
        added_in_version="1.0.0",
    ),
    "0907": DefaultRule(
        rule_id="0907",
        name="nested-for-loop",
        msg="Nested for loops are not supported. You can use keyword with for loop instead",
        severity=RuleSeverity.ERROR,
        version="<4.0",
        docs="""
        Older versions of Robot Framework did not support nested for loops::

            FOR    ${var}    IN RANGE    10
                FOR   ${other_var}   IN    a  b
                    # Nesting supported from Robot Framework 4.0+
                END
            END

        """,
        added_in_version="1.0.0",
    ),
    "0908": DefaultRule(
        rule_id="0908",
        name="if-can-be-used",
        msg="'{{ run_keyword }}' can be replaced with IF block since Robot Framework 4.0",
        severity=RuleSeverity.INFO,
        version="==4.*",
        docs="""
        Starting from Robot Framework 4.0 ``Run Keyword If`` and ``Run Keyword Unless`` can be replaced by IF block.
        """,
        added_in_version="1.4.0",
    ),
    "0909": DefaultRule(
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
        rule_id="0909",
        name="inconsistent-assignment",
        msg="The assignment sign is not consistent within the file. Expected '{{ expected_sign }}' "
        "but got '{{ actual_sign }}' instead",
        severity=RuleSeverity.WARNING,
        docs="""
        Use only one type of assignment sign in a file.

        Example of rule violation::

            *** Keywords ***
            Keyword
                ${var} =  Other Keyword
                No Operation

            Keyword 2
                No Operation
                ${var}  ${var2}  Some Keyword  # this assignment doesn't use equal sign while the previous one uses ' ='

        By default Robocop looks for most popular assignment sign in the file. It is possible to define expected
        assignment sign by running::

            robocop --configure inconsistent-assignment:assignment_sign_type:equal_sign

        You can choose between following signs: 'autodetect' (default), 'none', 'equal_sign' (``=``) or
        space_and_equal_sign (`` =``).

        """,
        added_in_version="1.7.0",
    ),
    "0910": DefaultRule(
        RuleParam(
            name="assignment_sign_type",
            default="autodetect",
            converter=parse_assignment_sign_type,
            show_type="assignment sign type",
            desc="possible values: 'autodetect' (default), 'none' (''), "
            "'equal_sign' ('=') or space_and_equal_sign (' =')",
        ),
        rule_id="0910",
        name="inconsistent-assignment-in-variables",
        msg="The assignment sign is not consistent inside the variables section. Expected '{{ expected_sign }}' "
        "but got '{{ actual_sign }}' instead",
        severity=RuleSeverity.WARNING,
        docs="""
        Use one type of assignment sign in Variables section.

        Example of rule violation::

            *** Variables ***
            ${var} =    1
            ${var2}=    2
            ${var3} =   3
            ${var4}     a
            ${var5}     b

        By default, Robocop looks for the most popular assignment sign in the file. It is possible to define expected
        assignment sign by running::

            robocop --configure inconsistent-assignment-in-variables:assignment_sign_type:equal_sign

        You can choose between following signs: 'autodetect' (default), 'none', 'equal_sign' (``=``) or
        space_and_equal_sign (`` =``).

        """,
        added_in_version="1.7.0",
    ),
    "0911": DefaultRule(
        rule_id="0911",
        name="wrong-import-order",
        msg="BuiltIn library import '{{ builtin_import }}' should be placed before '{{ custom_import }}'",
        severity=RuleSeverity.WARNING,
        docs="""
        Example of rule violation::

            *** Settings ***
            Library    Collections
            Library    CustomLibrary
            Library    OperatingSystem  # BuiltIn library defined after custom CustomLibrary

        """,
        added_in_version="1.7.0",
    ),
    "0912": DefaultRule(
        RuleParam(
            name="variable_source",
            default="section,var",
            converter=comma_separated_list,
            show_type="comma separated list",
            desc="Variable sources that will be checked",
        ),
        rule_id="0912",
        name="empty-variable",
        msg="Use built-in variable {{ var_type }}{EMPTY} instead of leaving variable without value or using backslash",
        severity=RuleSeverity.INFO,
        docs="""
        Variables with placeholder ${EMPTY} values are more explicit.

        Example of rule violation::

            *** Variables ***
            ${VAR_NO_VALUE}                   # missing value
            ${VAR_WITH_EMPTY}       ${EMPTY}
            @{MULTILINE_FIRST_EMPTY}
            ...                               # missing value
            ...  value
            ${EMPTY_WITH_BACKSLASH}  \\       # used backslash

            *** Keywords ***
            Create Variables
                VAR    ${var_no_value}  # missing value
                VAR    ${var_with_empty}    ${EMPTY}

        You can configure ``empty-variable`` rule to run only in ```*** Variables ***``` section or on
        ``VAR`` statements using ``variable_source`` parameter.
        """,
        added_in_version="1.10.0",
    ),
    "0913": DefaultRule(
        rule_id="0913",
        name="can-be-resource-file",
        msg="No tests in '{{ file_name }}' file, consider renaming to '{{ file_name_stem }}.resource'",
        severity=RuleSeverity.INFO,
        docs="""
        If the Robot file contains only keywords or variables, it's a good practice to use ``.resource`` extension.
        """,
        added_in_version="1.10.0",
    ),
    "0914": DefaultRule(
        rule_id="0914",
        name="if-can-be-merged",
        msg="IF statement can be merged with previous IF (defined in line {{ line }})",
        severity=RuleSeverity.INFO,
        version=">=4.0",
        docs="""
        ``IF`` statement follows another ``IF`` with identical conditions. It can be possibly merged into one.

        Example of rule violation::

            IF  ${var} == 4
                Keyword
            END
            # comments are ignored
            IF  ${var}  == 4
                Keyword 2
            END

        ``IF`` statement is considered identical only if all branches have identical conditions.

        Similar but not identical ``IF``::

            IF  ${variable}
                Keyword
            ELSE
                Other Keyword
            END
            IF  ${variable}
                Keyword
            END

        """,
        added_in_version="2.0.0",
    ),
    "0915": DefaultRule(
        rule_id="0915",
        name="statement-outside-loop",
        msg="{{ name }} {{ statement_type }} used outside a loop",
        severity=RuleSeverity.ERROR,
        version=">=5.0",
        docs="""
        Following keywords and statements should only be used inside loop (``WHILE`` or ``FOR``):
            - ``Exit For Loop``
            - ``Exit For Loop If``
            - ``Continue For Loop``
            - ``Continue For Loop If``
            - ``CONTINUE``
            - ``BREAK``

        """,
        added_in_version="2.0.0",
    ),
    "0916": DefaultRule(
        RuleParam(
            name="max_width",
            default=80,
            converter=int,
            desc="maximum width of IF (in characters) below which it will be recommended to use inline IF",
        ),
        SeverityThreshold("max_width", compare_method="less"),
        rule_id="0916",
        name="inline-if-can-be-used",
        msg="IF can be replaced with inline IF",
        severity=RuleSeverity.INFO,
        version=">=5.0",
        docs="""
        Short and simple ``IF`` statements can be replaced with ``inline IF``.

        Following ``IF``::

            IF    $condition
                BREAK
            END

        can be replaced with::

            IF    $condition    BREAK

        """,
        added_in_version="2.0.0",
    ),
    "0917": DefaultRule(
        rule_id="0917",
        name="unreachable-code",
        msg="Unreachable code after {{ statement }} statement",
        severity=RuleSeverity.WARNING,
        version=">=5.0",
        docs="""
        Detect the unreachable code after ``RETURN``, ``BREAK`` or ``CONTINUE`` statements.

        For example::

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

        """,
        added_in_version="3.1.0",
    ),
    "0918": DefaultRule(
        rule_id="0918",
        name="multiline-inline-if",
        msg="Avoid splitting inline IF to multiple lines",
        severity=RuleSeverity.WARNING,
        version=">=5.0",
        docs="""
        It's allowed to create ``inline IF`` that spans multiple lines, but it should be avoided,
        since it decreases readability. Try to use normal ``IF``/``ELSE`` instead.

        Bad::

            IF  ${condition}  Log  hello
            ...    ELSE       Log  hi!

        Good::

            IF  ${condition}    Log  hello     ELSE    Log  hi!

        or also good::

            IF  ${condition}
                Log  hello
            ELSE
                Log  hi!
            END
        """,
        added_in_version="3.1.0",
    ),
    "0919": DefaultRule(
        rule_id="0919",
        name="unused-argument",
        msg="Keyword argument '{{ name }}' is not used",
        severity=RuleSeverity.WARNING,
        docs="""
        Keyword argument was defined but not used::

            *** Keywords ***
            Keyword
                [Arguments]    ${used}    ${not_used}  # will report ${not_used}
                Log    ${used}
                IF    $used
                    Log    Escaped syntax is supported.
                END

            Keyword with ${embedded} and ${not_used}  # will report ${not_used}
                Log    ${embedded}

        """,
        added_in_version="3.2.0",
    ),
    "0920": DefaultRule(
        rule_id="0920",
        name="unused-variable",
        msg="Variable '{{ name }}' is assigned but not used",
        severity=RuleSeverity.INFO,
        docs="""
        Variable was assigned but not used::

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

    """,
        added_in_version="3.2.0",
    ),
    "0921": DefaultRule(
        rule_id="0921",
        name="argument-overwritten-before-usage",
        msg="Keyword argument '{{ name }}' is overwritten before usage",
        severity=RuleSeverity.WARNING,
        docs="""
        Keyword argument was overwritten before it is used::

            *** Keywords ***
            Overwritten Argument
                [Arguments]    ${overwritten}  # we do not use ${overwritten} value at all
                ${overwritten}    Set Variable    value  # we only overwrite it

        """,
        added_in_version="3.2.0",
    ),
    "0922": DefaultRule(
        rule_id="0922",
        name="variable-overwritten-before-usage",
        msg="Local variable '{{ name }}' is overwritten before usage",
        severity=RuleSeverity.WARNING,
        docs="""
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

        """,
        added_in_version="3.2.0",
    ),
    "0923": DefaultRule(
        rule_id="0923",
        name="unnecessary-string-conversion",
        msg="Variable '{{ name }}' in '{{ block_name }}' condition has unnecessary string conversion",
        severity=RuleSeverity.INFO,
        deprecated=True,
        version=">=4.0",
        docs="""
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
        """,
        added_in_version="4.0.0",
    ),
    "0924": DefaultRule(
        rule_id="0924",
        name="expression-can-be-simplified",
        msg="'{{ block_name }}' condition can be simplified",
        severity=RuleSeverity.INFO,
        version=">=4.0",
        docs="""
        Evaluated expression can be simplified. For example::

            *** Keywords ***
            Click On Element
                [Arguments]    ${locator}
                IF    ${is_element_visible}==${TRUE}    RETURN
                ${is_element_enabled}    Set Variable    ${TRUE}
                WHILE    ${is_element_enabled} != ${TRUE}
                    ${is_element_enabled}    Get Element Status    ${locator}
                END
                Click    ${locator}

        can be rewritten to::

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

        """,
        added_in_version="4.0.0",
    ),
    "0925": DefaultRule(
        rule_id="0925",
        name="misplaced-negative-condition",
        msg="'{{ block_name }}' condition '{{ original_condition }}' can be rewritten to '{{ proposed_condition }}'",
        severity=RuleSeverity.INFO,
        version=">=4.0",
        docs="""
        Position of not operator can be changed for better readability.

        For example::

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

        Can be rewritten to::

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

        """,
        added_in_version="4.0.0",
    ),
    "0926": DefaultRule(
        rule_id="0926",
        name="builtin-imports-not-sorted",
        msg="BuiltIn library import '{{ builtin_import }}' should be placed before '{{ previous_builtin_import }}'",
        severity=RuleSeverity.WARNING,
        added_in_version="5.2.0",
        docs="""
        Example of rule violation::

            *** Settings ***
            Library    OperatingSystem
            Library    Collections  # BuiltIn libraries imported not in alphabetical order

        """,
    ),
    "0927": DefaultRule(
        RuleParam(
            name="sections_order",
            default="documentation,tags,timeout,setup,template,keyword,teardown",
            converter=parse_test_case_order_param,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
        rule_id="0927",
        name="test-case-section-out-of-order",
        msg="'{{ section_name }}' is in wrong place of Test Case. "
        "Recommended order of elements in Test Cases: {{ recommended_order }}",
        severity=RuleSeverity.WARNING,
        added_in_version="5.3.0",
        docs="""
        Sections should be defined in order set by ``sections_order``
        parameter (default: ``documentation,tags,timeout,setup,template,keyword,teardown``).

        To change the default order use following option::

            robocop --configure test-case-section-out-of-order:sections_order:comma,separated,list,of,sections

        where section should be case-insensitive name from the list:
        documentation, tags, timeout, setup, template, keywords, teardown.
        Order of not configured sections is ignored.

        Example of rule violation::

            *** Test Cases ***
            Keyword After Teardown
                [Documentation]    This is test Documentation
                [Tags]    tag1    tag2
                [Teardown]    Log    abc
                Keyword1
        """,
    ),
    "0928": DefaultRule(
        RuleParam(
            name="sections_order",
            default="documentation,tags,arguments,timeout,setup,keyword,teardown",
            converter=parse_keyword_order_param,
            show_type="str",
            desc="order of sections in comma-separated list",
        ),
        rule_id="0928",
        name="keyword-section-out-of-order",
        msg="'{{ section_name }}' is in wrong place of Keyword. "
        "Recommended order of elements in Keyword: {{ recommended_order }}",
        severity=RuleSeverity.WARNING,
        added_in_version="5.3.0",
        docs="""
        Sections should be defined in order set by ``sections_order``
        parameter (default: ``documentation,tags,arguments,timeout,setup,keyword,teardown``).

        To change the default order use following option::

            robocop --configure keyword-section-out-of-order:sections_order:comma,separated,list,of,sections

        where section should be case-insensitive name from the list:
        documentation, tags, arguments, timeout, setup, keyword, teardown.
        Order of not configured sections is ignored.

        Example of rule violation::

            *** Keywords ***
            Keyword After Teardown
                [Documentation]    This is keyword Documentation
                [Tags]    tag1    tag2
                [Teardown]    Log    abc
                Keyword1
        """,
    ),
    "0929": DefaultRule(
        rule_id="0929",
        name="no-global-variable",
        msg="Don't set global variables outside the variables section",
        severity=RuleSeverity.WARNING,
        added_in_version="5.6.0",
        docs="""
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
        """,
    ),
    "0930": DefaultRule(
        rule_id="0930",
        name="no-suite-variable",
        msg="Don't use suite variables",
        severity=RuleSeverity.WARNING,
        added_in_version="5.6.0",
        docs="""
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
        """,
    ),
    "0931": DefaultRule(
        rule_id="0931",
        name="no-test-variable",
        msg="Don't use test/task variables",
        severity=RuleSeverity.WARNING,
        added_in_version="5.6.0",
        docs="""
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
        """,
    ),
    "0932": DefaultRule(
        rule_id="0932",
        name="undefined-argument-default",
        msg="Undefined argument default, use {{ arg_name }}=${EMPTY} instead",
        severity=RuleSeverity.ERROR,
        added_in_version="5.7.0",
        docs="""
        Keyword arguments can define a default value. Every time you call the keyword, you can
        optionally overwrite this default.

        When you use an argument default, you should be as clear as possible. This improves the
        readability of your code. The syntax ``${argument}=`` is unclear unless you happen to know
        that it is technically equivalent to ``${argument}=${EMPTY}``. To prevent people from
        misreading your keyword arguments, explicitly state that the value is empty using the
        built-in ``${EMPTY}`` variable.

        Example of a rule violation::

            *** Keywords ***
            My Amazing Keyword
                [Arguments]    ${argument_name}=
        """,
    ),
    "0933": DefaultRule(
        rule_id="0933",
        name="undefined-argument-value",
        msg="Undefined argument value, use {{ arg_name }}=${EMPTY} instead",
        severity=RuleSeverity.ERROR,
        added_in_version="5.7.0",
        docs="""
        When calling a keyword, it can accept named arguments.

        When you call a keyword, you should be as clear as possible. This improves the
        readability of your code. The syntax ``argument=`` is unclear unless you happen to know
        that it is technically equivalent to ``argument=${EMPTY}``. To prevent people from
        misreading your keyword arguments, explicitly state that the value is empty using the
        built-in ``${EMPTY}`` variable.

        If your argument is falsly flagged by this rule, escape the ``=`` character in your argument
        value by like so: ``\\=``.

        Example of a rule violation::

            My Amazing Keyword    argument_name=
        """,
    ),
}


class ReturnChecker(VisitorChecker):
    """Checker for [Return] and Return From Keyword violations."""

    reports = (
        "keyword-after-return",
        "empty-return",
    )

    def visit_Keyword(self, node):  # noqa: N802
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
                        "empty-return",
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
                "keyword-after-return",
                error_msg=error,
                node=token,
                col=token.col_offset + 1,
                end_col=token.end_col_offset + 1,
            )
        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword  # noqa: N815


class UnreachableCodeChecker(VisitorChecker):
    """Checker for unreachable code after RETURN, BREAK or CONTINUE statements."""

    reports = ("unreachable-code",)

    def visit_Keyword(self, node):  # noqa: N802
        statement_node = None

        for child in node.body:
            if isinstance(child, (RETURN_CLASSES.return_class, Break, Continue)):
                statement_node = child
            elif not isinstance(child, (EmptyLine, Comment, Teardown)) and statement_node is not None:
                token = statement_node.data_tokens[0]
                code_after_statement = child.data_tokens[0] if hasattr(child, "data_tokens") else child
                self.report(
                    "unreachable-code",
                    statement=token.value,
                    node=child,
                    col=code_after_statement.col_offset + 1,
                    end_col=child.end_col_offset + 1,
                )
                statement_node = None

        self.generic_visit(node)

    visit_If = visit_For = visit_While = visit_Try = visit_Keyword  # noqa: N815


class NestedForLoopsChecker(VisitorChecker):
    """
    Checker for not supported nested FOR loops.

    Deprecated in RF 4.0
    """

    reports = ("nested-for-loop",)

    def visit_ForLoop(self, node):  # noqa: N802
        # For RF 4.0 node is "For" but we purposely don't visit it because nested for loop is allowed in 4.0
        for child in node.body:
            if child.type == "FOR":
                token = child.get_token(Token.FOR)
                self.report("nested-for-loop", node=child, col=token.col_offset + 1, end_col=token.end_col_offset + 1)


class IfBlockCanBeUsed(VisitorChecker):
    """
    Checker for potential IF block usage in Robot Framework 4.0

    Run Keyword variants (Run Keyword If, Run Keyword Unless) can be replaced with IF in RF 4.0
    """

    reports = ("if-can-be-used",)
    run_keyword_variants = {"runkeywordif", "runkeywordunless"}

    def visit_KeywordCall(self, node):  # noqa: N802
        if not node.keyword:
            return
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.run_keyword_variants:
            col = keyword_col(node)
            self.report("if-can-be-used", run_keyword=node.keyword, node=node, col=col, end_col=col + len(node.keyword))


class ConsistentAssignmentSignChecker(VisitorChecker):
    """
    Checker for inconsistent assignment signs.

    By default, this checker will try to autodetect most common assignment sign (separately for *** Variables ***
    section and *** Test Cases ***, *** Keywords *** sections) and report any inconsistent type of sign in particular
    file.

    To force one type of sign type you, can configure two rules::

        --configure inconsistent-assignment:assignment_sign_type:{sign_type}
        --configure inconsistent-assignment-in-variables:assignment_sign_type:{sign_type}

    ``${sign_type}`` can be one of: ``autodetect`` (default), ``none`` (''), ``equal_sign`` ('='),
    ``space_and_equal_sign`` (' =').

    """

    reports = (
        "inconsistent-assignment",
        "inconsistent-assignment-in-variables",
    )

    def __init__(self):
        self.keyword_expected_sign_type = None
        self.variables_expected_sign_type = None
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.keyword_expected_sign_type = self.param("inconsistent-assignment", "assignment_sign_type")
        self.variables_expected_sign_type = self.param("inconsistent-assignment-in-variables", "assignment_sign_type")
        if "autodetect" in [
            self.param("inconsistent-assignment", "assignment_sign_type"),
            self.param("inconsistent-assignment-in-variables", "assignment_sign_type"),
        ]:
            auto_detector = self.auto_detect_assignment_sign(node)
            if self.param("inconsistent-assignment", "assignment_sign_type") == "autodetect":
                self.keyword_expected_sign_type = auto_detector.keyword_most_common
            if self.param("inconsistent-assignment-in-variables", "assignment_sign_type") == "autodetect":
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
                "inconsistent-assignment",
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
                var_token,
                self.variables_expected_sign_type,
                "inconsistent-assignment-in-variables",
            )
        return node

    def check_assign_type(self, token, expected, issue_name):
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


class SettingsOrderChecker(VisitorChecker):
    """
    Checker for settings order.

    BuiltIn libraries imports should always be placed before other libraries imports.
    """

    reports = (
        "wrong-import-order",
        "builtin-imports-not-sorted",
    )

    def __init__(self):
        self.libraries = []
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.libraries = []
        self.generic_visit(node)
        first_non_builtin = None
        previous_builtin = None
        for library in self.libraries:
            if first_non_builtin is None:
                if library.name not in STDLIBS:
                    first_non_builtin = library.name
            elif library.name in STDLIBS:
                lib_name = library.get_token(Token.NAME)
                self.report(
                    "wrong-import-order",
                    builtin_import=library.name,
                    custom_import=first_non_builtin,
                    node=library,
                    col=lib_name.col_offset + 1,
                    end_col=lib_name.end_col_offset + 1,
                )
            if library.name in STDLIBS:
                if previous_builtin is not None and library.name < previous_builtin.name:
                    lib_name = library.get_token(Token.NAME)
                    self.report(
                        "builtin-imports-not-sorted",
                        builtin_import=library.name,
                        previous_builtin_import=previous_builtin.name,
                        node=library,
                        col=lib_name.col_offset + 1,
                        end_col=lib_name.end_col_offset + 1,
                    )
                previous_builtin = library

    def visit_LibraryImport(self, node):  # noqa: N802
        if not node.name:
            return
        self.libraries.append(node)


class EmptyVariableChecker(VisitorChecker):
    """Checker for variables without value."""

    reports = ("empty-variable",)

    def __init__(self):
        self.visit_var_section = False
        self.visit_var = False
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        variable_source = self.param("empty-variable", "variable_source")
        self.visit_var_section = "section" in variable_source
        self.visit_var = "var" in variable_source
        self.generic_visit(node)

    def visit_VariableSection(self, node):  # noqa: N802
        if self.visit_var_section:
            self.generic_visit(node)

    def visit_KeywordSection(self, node):  # noqa: N802
        if self.visit_var:
            self.generic_visit(node)

    visit_TestCaseSection = visit_KeywordSection  # noqa: N815

    def visit_Variable(self, node):  # noqa: N802
        if get_errors(node):
            return
        if not node.value:  # catch variable declaration without any value
            self.report("empty-variable", var_type=node.name[0], node=node, end_col=node.end_col_offset)
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    "empty-variable",
                    var_type="$",
                    node=token,
                    lineno=token.lineno,
                    col=1,
                    end_col=token.end_col_offset + 1,
                )

    def visit_Var(self, node):  # noqa: N802
        if node.errors:
            return
        if not node.value:  # catch variable declaration without any value
            first_data = node.data_tokens[0]
            self.report(
                "empty-variable",
                var_type=node.name[0],
                node=first_data,
                col=first_data.col_offset + 1,
                end_col=first_data.end_col_offset + 1,
            )
        for token in node.get_tokens(Token.ARGUMENT):
            if not token.value or token.value == "\\":
                self.report(
                    "empty-variable",
                    var_type="$",
                    node=token,
                    lineno=token.lineno,
                    col=token.col_offset + 1,
                    end_col=token.end_col_offset + 1,
                )


class ResourceFileChecker(VisitorChecker):
    """Checker for resource files."""

    reports = ("can-be-resource-file",)

    def visit_File(self, node):  # noqa: N802
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
                self.report("can-be-resource-file", file_name=Path(source).name, file_name_stem=file_name, node=node)


class IfChecker(VisitorChecker):
    """Checker for IF blocks"""

    reports = (
        "if-can-be-merged",
        "inline-if-can-be-used",
        "multiline-inline-if",
    )

    def visit_TestCase(self, node):  # noqa: N802
        if get_errors(node):
            return
        self.check_adjacent_ifs(node)

    visit_For = visit_If = visit_Keyword = visit_TestCase  # noqa: N815  # TODO: While, Try Except?

    @staticmethod
    def is_inline_if(node):
        return isinstance(node.header, InlineIfHeader)

    def check_adjacent_ifs(self, node):
        previous_if = None
        for child in node.body:
            if isinstance(child, If):
                if child.header.errors:
                    continue
                self.check_whether_if_should_be_inline(child)
                if previous_if and child.header and self.compare_conditions(child, previous_if):
                    token = child.header.get_token(child.header.type)
                    self.report("if-can-be-merged", line=previous_if.lineno, node=token, col=token.col_offset + 1)
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

    def check_whether_if_should_be_inline(self, node):
        if ROBOT_VERSION.major < 5:
            return
        if self.is_inline_if(node):
            if node.lineno != node.end_lineno:
                if_header = node.header.data_tokens[0]
                self.report(
                    "multiline-inline-if",
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
        if min_possible > self.param("inline-if-can-be-used", "max_width"):
            return
        token = node.header.get_token(node.header.type)
        self.report("inline-if-can-be-used", node=node, col=token.col_offset + 1, sev_threshold_value=min_possible)


class LoopStatementsChecker(VisitorChecker):
    """Checker for loop keywords and statements such as CONTINUE or Exit For Loop"""

    reports = ("statement-outside-loop",)
    for_keyword = {"continueforloop", "continueforloopif", "exitforloop", "exitforloopif"}

    def __init__(self):
        self.loops = 0
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.loops = 0
        self.generic_visit(node)

    def visit_For(self, node):  # noqa: N802
        self.loops += 1
        self.generic_visit(node)
        self.loops -= 1

    visit_While = visit_For  # noqa: N815

    def visit_KeywordCall(self, node):  # noqa: N802
        if node.errors or self.loops:
            return
        if normalize_robot_name(node.keyword, remove_prefix="builtin.") in self.for_keyword:
            col = keyword_col(node)
            self.report(
                "statement-outside-loop",
                name=f"'{node.keyword}'",
                statement_type="keyword",
                node=node,
                col=col,
                end_col=col + len(node.keyword),
            )

    def visit_Continue(self, node):  # noqa: N802
        self.check_statement_in_loop(node, "CONTINUE")  # type: ignore[arg-type]

    def visit_Break(self, node):  # noqa: N802
        self.check_statement_in_loop(node, "BREAK")  # type: ignore[arg-type]

    def visit_Error(self, node):  # noqa: N802
        """Support for RF >= 6.1"""
        for error_token in node.get_tokens(Token.ERROR):
            if "is not allowed in this context" in error_token.error:
                self.report(
                    "statement-outside-loop",
                    name=error_token.value,
                    statement_type="statement",
                    node=node,
                    col=error_token.col_offset + 1,
                )

    def check_statement_in_loop(self, node, token_type):
        if self.loops or node.errors and f"{token_type} can only be used inside a loop." not in node.errors:
            return
        self.report(
            "statement-outside-loop",
            name=token_type,
            statement_type="statement",
            node=node,
            col=token_col(node, token_type),
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

    def visit_Variable(self, node):  # noqa: N802
        if get_errors(node):
            return
        var_token = node.get_token(Token.VARIABLE)
        variable_match = search_variable(var_token.value, ignore_errors=True)
        normalized = normalize_robot_name(variable_match.base)
        self.section_variables[normalized] = CachedVariable(variable_match.name, var_token, False)


class UnusedVariablesChecker(VisitorChecker):
    reports = (
        "unused-argument",
        "unused-variable",
        "argument-overwritten-before-usage",
        "variable-overwritten-before-usage",
    )

    def __init__(self):
        self.arguments: dict[str, CachedVariable] = {}
        self.variables: list[dict[str, CachedVariable]] = [
            {}
        ]  # variables are list of scope-dictionaries, to support IF branches
        self.section_variables: dict[str, CachedVariable] = {}
        self.used_in_scope = set()  # variables that were used in current FOR/WHILE loop
        self.ignore_overwriting = False  # temporarily ignore overwriting, e.g. in FOR loops
        self.in_loop = False  # if we're in the loop we need to check whole scope for unused-variable
        self.test_or_task_section = False
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.test_or_task_section = False
        section_variables = SectionVariablesCollector()
        section_variables.visit(node)
        self.section_variables = section_variables.section_variables
        self.generic_visit(node)
        self.report_not_used_section_variables()

    def report_not_used_section_variables(self):
        if not self.test_or_task_section:
            return
        self.check_unused_variables_in_scope(self.section_variables)

    def visit_TestCaseSection(self, node):  # noqa: N802
        self.test_or_task_section = True
        self.generic_visit(node)

    visit_TaskSection = visit_TestCaseSection  # noqa: N815

    def visit_TestCase(self, node):  # noqa: N802
        self.variables = [{}]
        self.generic_visit(node)
        self.check_unused_variables()

    def visit_Keyword(self, node):  # noqa: N802
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
                self.report_arg_or_var_rule("unused-argument", arg.token, value)
        self.check_unused_variables()
        self.arguments = {}

    def check_unused_variables(self):
        for scope in self.variables:
            self.check_unused_variables_in_scope(scope)

    def check_unused_variables_in_scope(self, scope):
        for variable in scope.values():
            if not variable.is_used:
                self.report_arg_or_var_rule("unused-variable", variable.token, variable.name)

    def report_arg_or_var_rule(self, rule, token, value=None):
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

    def add_argument(self, argument, normalized_name, token):
        self.arguments[normalized_name] = CachedVariable(argument, token, False)

    def parse_arguments(self, node):
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

    def parse_embedded_arguments(self, name_token):
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
            return node
        for token in node.header.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(token.value, is_var=False)
        self.variables.append({})
        for item in node.body:
            self.visit(item)
        self.add_variables_from_if_to_scope()
        if node.orelse:
            self.visit(node.orelse)
        for token in node.header.get_tokens(Token.ASSIGN):
            self.handle_assign_variable(token)

    def add_variables_from_if_to_scope(self):
        """
        Add all variables in given IF branch to common scope. If variable is used already in the branch, if it will
        also be mark as used.
        """
        variables = self.variables.pop()
        if not self.variables:
            self.variables.append(variables)
            return
        for var_name, cached_var in variables.items():
            if var_name in self.variables[-1]:
                if cached_var.is_used:
                    self.variables[-1][var_name].is_used = True
            else:
                self.variables[-1][var_name] = cached_var

    def visit_LibraryImport(self, node):  # noqa: N802
        for token in node.get_tokens(Token.NAME, Token.ARGUMENT):
            self.find_not_nested_variable(token.value, is_var=False)

    visit_TestTags = visit_ForceTags = visit_Metadata = visit_DefaultTags = visit_Variable = visit_ReturnStatement = (  # noqa: N815
        visit_ReturnSetting  # noqa: N815
    ) = visit_Teardown = visit_Timeout = visit_Return = visit_SuiteSetup = visit_SuiteTeardown = visit_TestSetup = (  # noqa: N815
        visit_TestTeardown  # noqa: N815
    ) = visit_Setup = visit_ResourceImport = visit_VariablesImport = visit_Tags = visit_Documentation = (  # noqa: N815
        visit_LibraryImport
    )

    def clear_variables_after_loop(self):
        """Remove used variables after loop finishes."""
        for index, scope in enumerate(self.variables):
            self.variables[index] = {name: variable for name, variable in scope.items() if not variable.is_used}

    def revisit_variables_used_in_loop(self):
        """
        Due to recursive nature of the loops, we need to revisit variables used in the loop again in case
        variable defined in the further part of the loop was used.

        For example::

            *** Keywords ***
            Use loop variable
                WHILE    ${True}
                    ${counter}    Update Counter    ${counter}
                END
        """
        for name in self.used_in_scope:
            self._set_variable_as_used(name, self.variables[-1])

    def visit_While(self, node):  # noqa: N802
        if node.header.errors:
            return node
        self.in_loop = True
        self.used_in_scope = set()
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
            return node
        self.in_loop = True
        self.used_in_scope = set()
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
            return node
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

    def visit_KeywordCall(self, node):  # noqa: N802
        for token in node.get_tokens(Token.ARGUMENT, Token.KEYWORD):  # argument can be used in keyword name
            self.find_not_nested_variable(token.value, is_var=False)
        for token in node.get_tokens(Token.ASSIGN):  # we first check args, then assign for used and then overwritten
            self.handle_assign_variable(token)

    def visit_Var(self, node):  # noqa: N802
        if node.errors:  # for example invalid variable definition like $var}
            return
        for arg in node.get_tokens(Token.ARGUMENT):
            self.find_not_nested_variable(arg.value, is_var=False)
        variable = node.get_token(Token.VARIABLE)
        if variable and _is_var_scope_local(node):
            self.handle_assign_variable(variable)

    def visit_TemplateArguments(self, node):  # noqa: N802
        for argument in node.data_tokens:
            self.find_not_nested_variable(argument.value, is_var=False)

    def handle_assign_variable(self, token):
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
            if not arg.is_used:
                self.report_arg_or_var_rule("argument-overwritten-before-usage", arg.token)
            arg.is_used = is_used = True
        else:
            is_used = False
        if not variable_match.items:  # not item assignment like ${var}[1] =
            variable_scope = self.variables[-1]
            if normalized in variable_scope:
                is_used = variable_scope[normalized].is_used
                if not variable_scope[normalized].is_used and not self.ignore_overwriting:
                    self.report_arg_or_var_rule(
                        "variable-overwritten-before-usage", variable_scope[normalized].token, variable_match.name
                    )
            else:  # check for attribute access like .lower() or .x
                for variable_scope in self.variables[::-1]:
                    base_name = self.search_by_removing_attr_access(normalized, variable_scope)
                    if base_name is not None:
                        variable_scope[base_name].is_used = True
                        self.variables[-1][normalized] = CachedVariable(variable_match.name, token, True)
                        return
        if self.in_loop:
            variable = CachedVariable(variable_match.name, token, is_used)
        else:
            variable = CachedVariable(variable_match.name, token, False)
        self.variables[-1][normalized] = variable

    def find_not_nested_variable(self, value, is_var):
        """
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

    def find_escaped_variables(self, value):
        """Find all $var escaped variables in the value string and process them."""
        for var in find_escaped_variables(value):
            self.update_used_variables(var)

    def update_used_variables(self, variable_name):
        """
        Remove used variable from the arguments and variables store.

        If the normalized variable name was already defined, we need to remove it to know which variables are not used.
        If the variable is not found, we try to remove possible attribute access from the name and search again.
        For example:

          arg.attr -> arg
          arg["value"] -> arg
        """
        normalized = normalize_robot_name(variable_name)
        self.used_in_scope.add(normalized)
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
            self.search_by_removing_attr_access(normalized_name, variable_scope)

    @staticmethod
    def search_by_removing_attr_access(variable_name, variable_scope) -> Optional[str]:
        """Search and remove variables from variable_scope by removing attribute access elements from the name."""
        for attr_access in (".", "[", "(", "%", "+", "-", "*", "/"):  # ${arg.attr}
            if attr_access in variable_name:
                name, _ = variable_name.split(attr_access, maxsplit=1)
                name = name.strip()
                if name in variable_scope:
                    variable_scope[name].is_used = True
                    return name
        return None


class ExpressionsChecker(VisitorChecker):
    reports = ("expression-can-be-simplified", "misplaced-negative-condition")
    QUOTE_CHARS = {"'", '"'}
    CONDITION_KEYWORDS = {"passexecutionif", "setvariableif", "shouldbetrue", "shouldnotbetrue", "skipif"}
    COMPARISON_SIGNS = {"==", "!="}
    EMPTY_COMPARISON = {"${true}", "${false}", "true", "false", "[]", "{}", "set()", "list()", "dict()", "0"}

    def visit_If(self, node):  # noqa: N802
        condition_token = node.header.get_token(Token.ARGUMENT)
        self.check_condition(node.header.type, condition_token, node.condition)
        self.generic_visit(node)

    visit_While = visit_If  # noqa: N815

    def visit_KeywordCall(self, node):  # noqa: N802
        normalized_name = normalize_robot_name(node.keyword, remove_prefix="builtin.")
        if normalized_name not in self.CONDITION_KEYWORDS:
            return
        condition_token = node.get_token(Token.ARGUMENT)
        self.check_condition(node.keyword, condition_token, condition_token.value)
        if normalized_name == "setvariableif":
            arguments = node.get_tokens(Token.ARGUMENT)
            if len(arguments) < 4:
                return
            for condition_token in arguments[2::2]:
                self.check_condition(node.keyword, condition_token, condition_token.value)

    def check_condition(self, node_name, condition_token, condition):
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

    def check_for_misplaced_not(self, condition_token, node_name, left_side, variable, right_side):
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
            "misplaced-negative-condition",
            block_name=node_name,
            original_condition=original_condition,
            proposed_condition=proposed_condition,
            node=condition_token,
            col=condition_token.col_offset + 1,
            end_col=condition_token.end_col_offset + 1,
        )

    def check_for_complex_condition(self, condition_token, node_name, left_side, variable, right_side, position):
        """Check if right side of the equation can be simplified."""
        if not right_side:
            return
        normalized = right_side.lower().lstrip()  # ' == ${TRUE}' -> '== ${true}'
        if len(normalized) < 3:
            if normalized == ")" and left_side.endswith("len("):
                self.report(
                    "expression-can-be-simplified",
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
                "expression-can-be-simplified",
                block_name=node_name,
                node=condition_token,
                col=position,
                end_col=position + len(variable) + len(right_side),
            )


class TestAndKeywordOrderChecker(VisitorChecker):
    reports = ("test-case-section-out-of-order", "keyword-section-out-of-order")

    def __init__(self):
        self.rules_by_node_type = {}
        self.expected_order = {}
        super().__init__()

    def visit_File(self, node):  # noqa: N802
        self.rules_by_node_type = {Keyword: "keyword-section-out-of-order", TestCase: "test-case-section-out-of-order"}
        self.expected_order = {
            Keyword: self.param("keyword-section-out-of-order", "sections_order"),
            TestCase: self.param("test-case-section-out-of-order", "sections_order"),
        }
        self.generic_visit(node)

    def check_order(self, node):
        max_order_indicator = -1
        for subnode in node.body:
            try:
                subnode_type = subnode.type
            except AttributeError:
                continue
            if subnode_type not in self.expected_order[type(node)]:
                continue
            this_node_expected_order = self.expected_order[type(node)].index(subnode.type)
            if this_node_expected_order < max_order_indicator:
                self.report(
                    self.rules_by_node_type[type(node)],
                    section_name=subnode_type,
                    recommended_order=", ".join(self.expected_order[type(node)]),
                    node=subnode,
                    col=subnode.col_offset + 1,
                    end_col=subnode.end_col_offset + 1,
                )
            else:
                max_order_indicator = this_node_expected_order

    visit_Keyword = visit_TestCase = check_order  # noqa: N815


class NonLocalVariableChecker(VisitorChecker):
    reports = (
        "no-global-variable",
        "no-suite-variable",
        "no-test-variable",
    )
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
            self._report("no-global-variable", keyword_token)
            return

        if keyword_name == "setsuitevariable":
            self._report("no-suite-variable", keyword_token)
            return

        if keyword_name in ["settestvariable", "settaskvariable"]:
            self._report("no-test-variable", keyword_token)
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
            self._report("no-global-variable", option_token)
            return

        if scope in ["SUITE", "SUITES"]:
            self._report("no-suite-variable", option_token)
            return

        if scope in ["TEST", "TASK"]:
            self._report("no-test-variable", option_token)
            return

        # Unexpected scope, or variable-defined scope

    def _report(self, rule_name: str, node):
        self.report(
            rule_name,
            node=node,
            lineno=node.lineno,
            col=node.col_offset + 1,
            end_col=node.col_offset + len(node.value) + 1,
        )


class UndefinedArgumentDefaultChecker(VisitorChecker):
    reports = (
        "undefined-argument-default",
        "undefined-argument-value",
    )

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
                    "undefined-argument-default",
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
                "undefined-argument-value",
                node=token,
                lineno=token.lineno,
                col=token.col_offset + 1,
                end_col=token.col_offset + len(token.value) + 1,
                arg_name=arg_name,
            )
