*** Keywords ***
Keyword With Arguments
    [Arguments]    ${arg}    ${typed_arg: int}    ${_ignored}
    Log    ${arg} ${typed_arg}

Keyword With Default Values
    [Arguments]    ${arg}=default    ${typed_arg: str}=default
    Log    ${arg} ${typed_arg}

Keyword With All Types
    [Arguments]    ${positional}    @{varargs}    &{kwargs}
    Log    ${positional} @{varargs} &{kwargs}

# Negative tests - should NOT report and not throw exceptions

Keyword With Non Variable Argument
    # Not a valid variable syntax, should be ignored
    [Arguments]    ${var}    value=3
    Log    ${var}

Keyword With Missing Dollar Sign
    # Invalid variable syntax, should be ignored
    [Arguments]    {var}
    Log    Invalid

Keyword With Duplicate Arguments
    # Duplicate arguments - should still report on both if not typed
    [Arguments]    ${var}    ${var}
    Log    ${var}

Keyword With Multiline Arguments
    # Should report on correct line for each argument
    [Arguments]    ${arg1: int}
    ...    ${arg2}
    ...    ${arg3: str}
    ...    ${arg4}
    Log    ${arg1} ${arg2} ${arg3} ${arg4}
