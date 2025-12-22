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
