*** Test Cases ***
If condition
    IF    ${status} == ${TRUE}
        Log    ${variable}
    ELSE IF    ${status} == ${false}
        Log    ${variable}
        IF    ${status} != ${true}
            Log    ${variable}
        END
    END
    IF    ${status} == "${TRUE}""
        Log    ${variable}
    END
    ${assign}    IF    $class.attr == ${TRUE}    Set Variable    10    ELSE    Set Variable    20  # $var not recognized for now

While condition
    WHILE    ${status} == ${TRUE}    limit=1 min
        WHILE    ${status} != ${true}
            Log    ${variable}
        END
    END
    WHILE
        WHILE    TRUE
            Log    Still valid.
        END
    END

Keywords With Conditions
    Set Variable If    len(@{list})
    ...    value
    ...    not ${variable} == []
    ...    value
    ...    ${class.attr['item']} != set()
    ...    value
    Skip If    ${true}
    Skip If    ${variable} != ${truE}
    Should Be True    ${flag} == False

Empty Set Variable If
    ${var}    Set Variable If

Empty IF
    IF
    END
