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

Keywords With Conditions
    Pass Execution If    "${variable}" == "word"
    ${assign}    Set Variable If    "${variable}" == "word"    value
    Set Variable If    "${variable}" == "word"    value
    Set Variable If    "${variable}" == "word"    value    valueiffalse
    Set Variable If    "${variable}" == "word"    value    "${variable}" != "word"    not_value
    IF    $condition
        Should Be True    $variable == "word"
        Should Be True    '''${variable}''' == "word"
    END
    Should Not Be True    $variable == "word"
    Should Not Be True    '''${variable}''' == "word"
    Skip If    "${variable}" == "word"

Environment Variable
    IF    ""%{ENV_VAR}""
        Log    Such variable is always string and there is no conversion.
    END