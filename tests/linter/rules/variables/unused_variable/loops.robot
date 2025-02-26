*** Keywords ***
Keyword With While
    ${counter}    Set Variable    1
    Log    ${counter}    # used before loop
    WHILE    ${counter} < 10
        Log To Console    ${counter}
        ${counter}    Evaluate ${counter} + 1  # reassigned and used in the loop
    END
    ${counter}    Set Variable    1    # reassigned and not used

Keyword With While 2
    ${condition}    Get Condition
    WHILE    $condition
        ${not_used}    Keyword
    END

Keyword With While 3
    ${value}    Set Variable    10
    WHILE    $value
        ${value}    Keyword  # reassigned and not used
    END

Keyword With While 3
    ${value}    Set Variable    10
    Log    ${value}   # used
    WHILE    $value
        ${value}    Keyword  # reassigned but used
    END
    Log    ${value}    # used

Keyword With FOR
    ${variable}    Set Initial Value
    FOR    ${i}    IN RANGE    10
        Log To Console    ${i}
        Process    ${variable}
        ${variable}    Get New Value
    END

Used variable from arguments
    [Arguments]    ${counter}
    WHILE    ${counter} < 10
        Log To Console    ${counter}
        ${counter}    Evaluate    ${counter} + 1
    END

Used variable from arguments 2
    [Arguments]    ${counter}
    WHILE    ${counter} < 10
        Log    Used only in condition.
    END

Loop Header From Arguments And Global Count
    [Arguments]    ${list}
    FOR    ${item}    IN    @{list}
        Set To Dictionary    ${item}    displayOrder=${count}
        ${count}    Evaluate    ${count} + 1
    END
