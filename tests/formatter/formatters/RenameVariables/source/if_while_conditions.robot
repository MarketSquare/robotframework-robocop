*** Keywords ***
IF
    IF    ${variable}
        ${variable2}    Set Variable    10
    ELSE IF    '${variable2}' == '${5}'
        No Operation
    ELSE IF    ${ _global VARIABLE }    <    ${variable2}
        Log    ${global variable}
    ELSE
        No Operation
    END

Inline IF
    ${assign}    IF   $var    Keyword    ${arg}
    Log    Sentence with ${assign}

While
    WHILE    ${flag}
        ${value}    Keyword
        WHILE    ${value}
            No Operation
        END
    END
