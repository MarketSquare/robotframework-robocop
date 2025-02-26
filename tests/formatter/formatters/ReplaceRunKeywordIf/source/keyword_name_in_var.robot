*** Keywords ***
Keyword with variable for keyword name
    [Documentation]    Keyword documentation.
    [Arguments]    ${kw}    @{args}
    ${data} =    Run Keyword If    '${VARIABLE}'!='VALUE' and '${OTHER_VARIABLE}'!='VALUE'
    ...     ${kw}    @{args}
