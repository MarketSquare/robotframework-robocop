*** Keywords ***
Keyword with variable for keyword name
    [Documentation]    Keyword documentation.
    [Arguments]    ${kw}    @{args}
    IF    '${VARIABLE}'!='VALUE' and '${OTHER_VARIABLE}'!='VALUE'
        ${data} =    Run Keyword    ${kw}    @{args}
    ELSE
        ${data} =    Set Variable    ${None}
    END
