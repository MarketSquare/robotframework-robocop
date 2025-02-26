*** Test Cases ***
Test
    ${var}    ${var}    My Keyword
    FOR  ${i}  IN RANGE  10
        ${var}    ${var}    My Keyword
    END
    IF    ${condition}
        IF    ${condition}
            ${var}    ${var}    My Keyword
        ELSE IF
            ${var}    ${var}    My Keyword
        END
    END

*** Keywords ***
Keyword1
    [Arguments]    ${var}    ${var}    ${var2}
    ...    ${var}    ${Var}    ${var}=value
    ${var}    My Keyword
    ${var}    My Keyword    ${var}
    ${var}    ${var2}    ${var}    My Keyword    ${var}
    ${var}    ${Va r}    My Keyword    ${var}
    ${var}
    ...    ${var}    My Keyword    ${var}

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

Duplicated With Equal Sign
    ${duplicate}    ${duplicate}=    Keyword

Non Important Variable
    ${_}    ${middle}    ${_}    Unpack Tuple
    ${_}    ${middle}    ${_}=    Unpack Tuple
