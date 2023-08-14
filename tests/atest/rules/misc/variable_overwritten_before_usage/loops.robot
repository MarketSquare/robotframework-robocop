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

Each Try Branch Is Separate Scope
    TRY
        ${variable}    Set Variable    value
    EXCEPT    Error message
        ${variablE}    Error Handler 1
        ${variable}    Error Handler 2
    EXCEPT    Another error    # comment
        ${variable}    Error Handler 2
    EXCEPT    ${message}       # match with variable
        ${Variable}    Error Handler 3
    ELSE
        ${variable}    Set Variable    value
    FINALLY
        ${variable}    Set Variable    value  # technically FINALLY should be in the same scope as all try/excepts
    END
