*** Test Cases ***
If condition
    IF    ${status} is ${TRUE}
        Log    ${variable}
    ELSE IF    not ${status} is ${false}
        Log    ${variable}
        IF    not ${status} is ${NONE}
            Log    ${variable}
        END
    END
    IF    ${status} == "${TRUE}""
        Log    ${variable}
    END
    ${assign}    IF    $class.attr == ${TRUE}    Set Variable    10    ELSE    Set Variable    20  # $var not recognized for now

While condition
    WHILE    not ${status} is ${variable}    limit=1 min
        WHILE    not not ${status} is None
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
    ...    not ${status} is None
    ...    value
    ...    not ${class.attr['item']} is set()
    ...    value
    Skip If    ${true}
    Skip If    not ${status} is None
    Should Be True    not ${status} is None
