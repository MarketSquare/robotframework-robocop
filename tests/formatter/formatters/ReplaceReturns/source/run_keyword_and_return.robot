*** Test Cases ***
For and Ifs
    FOR    ${var}  IN  1  2
        IF    $var == 2
            Run Keyword And Return    Keyword   ${arg}
        END
    END

*** Keywords ***
Testing
    Run Keyword And Return    Keyword   ${arg}
    ...  ${arg2}
