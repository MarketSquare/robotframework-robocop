*** Keywords ***
Keyword1
    [Arguments]    ${var}    ${var}    ${var2}
    ...    ${var}    ${Var}    ${var}=value
    Log  ${var}

Keyword2
    [Arguments]    ${var}
    Log  ${var}

Keyword3
    Log  ${var}

Keyword4
    [Arguments]    %{var}    ${PARAM}    ${PARAM}
    Log  ${var}

Keyword5
    [Arguments]    var
    Log  ${var}
