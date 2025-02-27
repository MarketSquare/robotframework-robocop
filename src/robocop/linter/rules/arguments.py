from robocop.linter.rules import Rule, RuleParam, RuleSeverity


class UnusedArgumentRule(Rule):
    """
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

    """

    name = "unused-argument"
    rule_id = "ARG01"
    message = "Keyword argument '{name}' is not used"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"


class ArgumentOverwrittenBeforeUsageRule(Rule):
    """

    Keyword argument was overwritten before it is used::

        *** Keywords ***
        Overwritten Argument
            [Arguments]    ${overwritten}  # we do not use ${overwritten} value at all
            ${overwritten}    Set Variable    value  # we only overwrite it

    """

    name = "argument-overwritten-before-usage"
    rule_id = "ARG02"
    message = "Keyword argument '{name}' is overwritten before usage"
    severity = RuleSeverity.WARNING
    added_in_version = "3.2.0"


class UndefinedArgumentDefaultRule(Rule):
    """
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

    """

    name = "undefined-argument-default"
    rule_id = "ARG03"
    message = "Undefined argument default, use {arg_name}=${{EMPTY}} instead"
    severity = RuleSeverity.ERROR
    added_in_version = "5.7.0"


class UndefinedArgumentValueRule(Rule):
    r"""
    When calling a keyword, it can accept named arguments.

    When you call a keyword, you should be as clear as possible. This improves the
    readability of your code. The syntax ``argument=`` is unclear unless you happen to know
    that it is technically equivalent to ``argument=${EMPTY}``. To prevent people from
    misreading your keyword arguments, explicitly state that the value is empty using the
    built-in ``${EMPTY}`` variable.

    If your argument is falsely flagged by this rule, escape the ``=`` character in your argument
    value by like so: ``\=``.

    Example of a rule violation::

        *** Test Cases ***
        Test case
            My Amazing Keyword    argument_name=

    """

    name = "undefined-argument-value"
    rule_id = "ARG04"
    message = "Undefined argument value, use {arg_name}=${{EMPTY}} instead"
    severity = RuleSeverity.ERROR
    added_in_version = "5.7.0"


class InvalidArgumentsRule(Rule):
    """
    Argument names should follow variable naming syntax: start with identifier (``$``, ``@`` or ``&``) and enclosed
    in curly brackets (``{}``).

    Valid names::

        *** Test Cases ***
        Test case
            Keyword
                [Arguments]    ${var}    @{args}    &{config}    ${var}=default

    Invalid names::

        *** Test Cases ***
        Test case
            Keyword
                [Arguments]    {var}    @args}    var=default

    """

    name = "invalid-argument"
    rule_id = "ARG05"
    message = "{error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"


class DuplicatedArgumentRule(Rule):
    """
    Argument name is already used.

    Variable names in Robot Framework are case-insensitive and ignores spaces and underscores. Following arguments
    are duplicates::

        *** Keywords ***
        Keyword
            [Arguments]    ${var}  ${VAR}  ${v_ar}  ${v ar}
            Other Keyword

    """

    name = "duplicated-argument-name"
    rule_id = "ARG06"
    message = "Argument name '{argument_name}' is already used"
    severity = RuleSeverity.ERROR
    added_in_version = "1.11.0"


class ArgumentsPerLineRule(Rule):
    """
    Too many arguments per continuation line.

    If the keyword's ``[Arguments]`` are split into multiple lines, it is recommended to put only one argument
    per every line.

    Incorrect code example::

        *** Keywords ***
        Keyword With Multiple Arguments
        [Arguments]    ${first_arg}
        ...    ${second_arg}    ${third_arg}=default

    Correct code::

        *** Keywords ***
        Keyword With Multiple Arguments
        [Arguments]    ${first_arg}
        ...    ${second_arg}
        ...    ${third_arg}=default

    """

    name = "arguments-per-line"
    rule_id = "ARG07"
    message = "There is too many arguments per continuation line ({arguments_count} / {max_arguments_count})"
    severity = RuleSeverity.INFO
    parameters = [
        RuleParam(
            name="max_args",
            default=1,
            converter=int,
            desc="maximum number of arguments allowed in the continuation line",
        ),
    ]
    # TODO flag to allow for [Arguments] multiple args ine one line, just not in other ...
