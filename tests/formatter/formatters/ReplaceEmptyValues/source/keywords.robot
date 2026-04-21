*** Keywords ***
Keyword With Empty Vars
    VAR    ${empty_scalar}
    VAR    @{empty_list}
    VAR    &{empty_dict}
    VAR    ${empty_scalar_cont}
    ...
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
