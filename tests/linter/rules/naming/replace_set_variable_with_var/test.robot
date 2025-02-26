*** Test Cases ***
Test with Set Variables
    Set Local Variable    $variable
    Set Global Variable    ${variable}
    Set Test Variable    ${variable}    value
    FOR    ${v}    IN    a  b
        Set Task Variable    ${v}
        IF    $v
            Set Suite Variable    ${SUITE_VAR}
        END
    END
    VAR    ${var}


*** Keywords ***
Keyword With Set Variables
    Set Local Variable    $variable
    Setglobal Variable    ${variable}
    Set Test Variable    ${variable}    value
    TRY
        Set_Task Variable    ${v}
    EXCEPT
        Set Suite Variable    ${SUITE_VAR}
    END
    VAR    ${var}
