*** Keywords ***
Keyword With Empty Vars
    VAR    ${empty_scalar}    ${EMPTY}
    VAR    @{empty_list}    @{EMPTY}
    VAR    &{empty_dict}    &{EMPTY}
    VAR    ${scalar}    value
    VAR    @{list}    item1    item2
    VAR    &{dict}    key=value
    Log    ${empty_scalar}

Keyword With Traditional VAR
    [Documentation]    Test with traditional Set Variable
    ${empty}    Set Variable
    ${filled}    Set Variable    value
    RETURN    ${empty}

Keyword With Empty Assignment
    ${var1}    ${var2}    ${var3}    Get Multiple Values
    Log Many    ${var1}    ${var2}    ${var3}
