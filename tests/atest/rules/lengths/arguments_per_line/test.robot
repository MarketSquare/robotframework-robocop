*** Keywords ***
Keyword Without Arguments
    No Operation

Keyword With Empty Arguments
    [Arguments]
    No Operation

Keyword With Arguments In One Line
    [Arguments]  ${arg}    ${arg2}    ${arg3}
    No Operation

Keyword With Arguments In Multiple Lines - Good
    [Arguments]      ${arg}
    ...    ${arg2}
    ...    ${arg3}
    No Operation

Keyword With Arguments In Multiple Lines - Bad
    [Arguments]  ${arg}
    ...    ${arg2}    ${arg3}
    No Operation

Keyword With Arguments In Multiple Lines - Bad 2
    [Arguments]  ${arg}
    ...    ${arg2}    ${arg3}    ${arg4}=default
    No Operation

Keyword With Arguments In Multiple Lines - Bad 3
    [Arguments]  ${arg}
    ...    ${arg2}    ${arg3}
    # ... it works for all except RF 4.0 which has critical bug on empty arguments
    ...    ${arg5}    ${arg6}
    No Operation

Keyword With Arguments In Multiple Lines - Bad 4
    [Arguments]  ${arg}    ${arg2}
    ...    ${arg3}
    No Operation

Keyword With ${embedded} Arguments
    Should Be Ignored
