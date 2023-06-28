*** Test Cases ***
If condition
    IF    "${variable}" == "word"
        Log    ${variable}
    ELSE IF    r'''${variable}''' == "word"
        Log    ${variable}
        IF    "${variable}" == "word"
            Log    ${variable}
        END
    END
    IF    ${variable} == "word"
        Log    ${variable}
    END
    IF    $variable == "word"
        Log    ${variable}
    END
    ${assign}    IF    '${variable}'    Set Variable    10    ELSE IF    "${string_var}" != "value"    Set Variable    20

While condition
    WHILE    "${variable}" == "word"    limit=1 min
        WHILE    "${variable}" == "word"
            Log    ${variable}
        END
    END
    WHILE
        WHILE    TRUE
            Log    Still valid.
        END
    END
