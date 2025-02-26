*** Test Cases ***
Inline IF
    IF   ${condition}   Keyword   ${arg}
    ${assign}   IF    $flag   Other Keyword    ${argument}    ELSE       Set Variable   ${None}

TRY
    TRY
        ${variable}             Keyword                 ${var}
    EXCEPT    Error
        ${variable}             Keyword                 ${var}
    ELSE
        ${variable}             Keyword                 ${var}
    FINALLY
        ${variable}             Keyword                 ${var}
    END

While
    WHILE    ${condition}
        ${variable}             Keyword                 ${var}
    END
