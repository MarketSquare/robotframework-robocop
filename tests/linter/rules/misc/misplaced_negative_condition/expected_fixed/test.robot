*** Test Cases ***
If condition
    IF    ${status} is ${TRUE}
        Log    ${variable}
    ELSE IF    ${status} is not ${false}
        Log    ${variable}
        IF    ${status} is not ${NONE}
            Log    ${variable}
        END
    END
    IF    ${status} == "${TRUE}""
        Log    ${variable}
    END
    ${assign}    IF    $class.attr == ${TRUE}    Set Variable    10    ELSE    Set Variable    20  # $var not recognized for now

While condition
    WHILE    ${status} is not ${variable}    limit=1 min
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
    ...    ${status} is not None
    ...    value
    ...    ${class.attr['item']} is not set()
    ...    value
    Skip If    ${true}
    Skip If    ${status} is not None
    Should Be True    ${status} is not None
