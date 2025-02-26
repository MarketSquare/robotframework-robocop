*** Keywords ***
With Set Variable Workaround
    IF    r'''${var}''' == 'True'
        ${var}    My Keyword
    ELSE IF    ${var}==2
        ${var}    My Other Keyword
    END

    IF    r'''${var}''' == 'True'
        ${var}    ${var2}    My Keyword
    END

    IF    r'''${var}''' == 'True'
        ${var}    ${var2}    My Keyword
    ELSE
        ${var}    ${var2}    Set Variable    ${var2}    ${var}
    END

    IF    r'''${var}''' == 'True'
        ${var}    ${var2}    My Keyword
    ELSE
        ${var}    ${var2}    Set Variable    ${var2}
    END
