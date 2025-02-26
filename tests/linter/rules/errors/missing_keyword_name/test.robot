*** Keywords ***
Keyword
    var
    ${var}
    ${one}      ${two}
    ${var}var
    ${var} var
    ${var}Var
    ${var} Var

Nested in blocks
    IF    $condition
        ${var}
    END
    FOR    ${var}    IN RANGE  10
        ${var}
    END
    WHILE    $condition
        ${var}
    END
    TRY
        ${var}
    EXCEPT
        Keyword
    ELSE
        Keyword
    FINALLY
        ${var}
    END

Group
    GROUP    Missing keyword name
       ${var}
    END
