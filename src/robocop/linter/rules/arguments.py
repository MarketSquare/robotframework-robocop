from robocop.linter.rules import Rule, RuleSeverity


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

        Keyword
            [Arguments]    ${var}    @{args}    &{config}    ${var}=default

    Invalid names::

        Keyword
            [Arguments]    {var}    @args}    var=default

    """

    name = "invalid-argument"
    rule_id = "ARG05"
    message = "{error_msg}"
    severity = RuleSeverity.ERROR
    version = ">=4.0"
    added_in_version = "1.11.0"
