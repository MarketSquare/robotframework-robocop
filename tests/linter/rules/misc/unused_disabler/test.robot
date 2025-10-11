*** Test Cases ***
Inline disablers - not used
    No Operation  # robocop: off=NAME01
    No Operation  # robocop: off=wrong-case-in-keyword-name
    FOR    ${var}    IN    @{LIST}    # robocop: off=unused-variable
        Log    ${var}
    END
    Log    ${var}  # robocop: off

Inline disablers - .used  # robocop: off=NAME01
    No operation  # robocop: off=wrong-case-in-keyword-name
    FOR    ${var}    IN    @{LIST}    # robocop: off=unused-variable
        Log    I dont use var
    END

Multiple disablers - not used
    No Operation  # robocop: off=NAME01,unused-variable  some-text robocop: off=some-rule

Multiple disablers - partly used
    ${var}    Set Variable    value  # robocop: off=some-rule,unused-variable

Multiline disablers - not used
    # robocop: off=unused-variable
    ${var}    Set Variable    value
    Log    ${var}
    # robocop: on=unused-variable
    ${var2}    Set Variable    value
    IF    $condition
        # robocop: off=SPC10
        No Operation
    END

Multiline disablers - used
    # robocop: off=unused-variable
    ${var}    Set Variable    value
    # robocop: on=unused-variable
    ${var2}    Set Variable    value
    IF    $condition
        # robocop: off=multiline-inline-if
        IF  ${condition}  Log  hello
        ...    ELSE       Log  hi!
    END

Multiline disablers - partly used
    # robocop: off=unused-variable,some-rule
    ${var}    Set Variable    value
    # robocop: on
    ${var2}    Set Variable    value

Noqa
    ${var}    Set Variable    value  # noqa
    ${var2}    Set Variable    value  # noqa
    Log    ${var}


*** Keywords ***
Used But Excluded Globally
    [Arguments]    ${arg1}    ${arg2}    ${arg3}    ${arg4}    ${arg5}    ${arg6}  # robocop: off=too-many-arguments

Disabled With All And Selected Rule
    # robocop: off
    # robocop: off=unused-variable
    ${var}    Set Variable    value

Disabled All Unused
    # robocop: off
    No Operation
