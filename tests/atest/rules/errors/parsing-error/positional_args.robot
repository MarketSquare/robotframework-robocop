*** Keywords ***
Keyword
    [Arguments]    ${arg}=3    ${arg2}    ${arg3}  # invalid
    Log  ${arg}
    Log  ${arg2}

Keyword With Mixed Arguments
    [Arguments]    ${arg}=3    ${arg2}     ${arg4}=5    ${arg1}
    No Operation

Keyword With Kwargs
    [Arguments]  &{kwargs}  @{args}  ${arg}
    No Operation
