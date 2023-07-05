*** Test Cases ***
If condition
    IF    ${status} is not ${TRUE}
        Log    ${variable}
    ELSE IF    not ${status} is not not ${false}
        Log    ${variable}
        IF    not not ${status} is ${NONE}
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
    ...    not ${status} is not None
    ...    value
    ...    not not ${class.attr['item']} is set()
    ...    value
    Skip If    ${true}
    Skip If    not ${status} is not not None
    Should Be True    not ${status} is None
