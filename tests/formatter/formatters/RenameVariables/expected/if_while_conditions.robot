*** Keywords ***
IF
    IF    ${VARIABLE}
        ${variable2}    Set Variable    10
    ELSE IF    '${variable2}' == '${5}'
        No Operation
    ELSE IF    ${GLOBAL_VARIABLE}    <    ${variable2}
        Log    ${GLOBAL_VARIABLE}
    ELSE
        No Operation
    END

Inline IF
    ${assign}    IF   $var    Keyword    ${ARG}
    Log    Sentence with ${assign}

While
    WHILE    ${FLAG}
        ${value}    Keyword
        WHILE    ${value}
            No Operation
        END
    END
