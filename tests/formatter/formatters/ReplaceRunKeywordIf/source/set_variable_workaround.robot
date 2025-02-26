*** Keywords ***
With Set Variable Workaround
    ${var}    Run Keyword If    r'''${var}''' == 'True'    My Keyword
    ...  ELSE IF    ${var}==2    My Other Keyword
    ...  ELSE    Set Variable    ${var}

    ${var}    ${var2}    Run Keyword If    r'''${var}''' == 'True'    My Keyword
    ...  ELSE    Set Variable    ${var}    ${var_2}

    ${var}    ${var2}    Run Keyword If    r'''${var}''' == 'True'    My Keyword
    ...  ELSE    Set Variable    ${var2}    ${var}

    ${var}    ${var2}    Run Keyword If    r'''${var}''' == 'True'    My Keyword
    ...  ELSE    Set Variable    ${var2}
