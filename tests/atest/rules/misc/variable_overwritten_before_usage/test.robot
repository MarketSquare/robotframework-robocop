*** Variables ***
${VARIABLE}    value


*** Keywords ***
Overwritten Variable
    ${value}    Keyword
    ${value}    Keyword

Used And Overwritten
    ${value}    Keyword
    ${value}    Keyword    ${value}  # should not report anything

Overwritten IF assign
    ${value} =    IF    $condition    Keyword
    ${val_ue}    Keyword

Overwritten In FOR
    # should ignore for variables, it's normal to init variable in case FOR does not run
    ${variable}=    Keyword
    ...    ${GLOBAL}
    FOR    ${variable}    IN RANGE    10
        Log    ${variable}
    END

Defined In Both IF Branches
    ${overwritten}    Keyword
    IF   $required is None
        ${longitude}=    Create Dictionary    key=longitude    type=float    required=${None}  # should not be reported
    ELSE
        ${longitude}=    Create Dictionary    key=longitude    type=float    required=${True}
        ${overwritten}    Keyword
    END

No Arguments
    ${value}    Keyword Call    ${VARIABLE}

Overwritten Argument
    [Arguments]    ${arg1}    ${overwritten1}    ${overwritten2}    ${overwritten3}    ${overwritten_but_used}
    ${overwritten1}    Set Variable    ${arg1}
    ${overwritten2}    Set Variable    ${arg1}
    ${overwritten_but_used}    Keyword    String with ${overwritten_but_used}
    Keyword Call    ${overwritten1}  # used, but by overwritten
    Keyword Call    ${overwritten2}  # used, but by overwritten
    FOR    ${overwritten3}    IN    @{arg1}
        Log    ${overwritten3}
    END

Argument In String
    [Arguments]    ${used}    ${not_used}
    Keyword Call
    ...    Sentence with ${used} argument

Nested Arguments
    [Arguments]    ${used}    ${used2}    ${not_used}
    Keyword Call    ${name_${used}}
    Keyword Call    ${variable}[${used2}]

Args And Kwargs
    [Arguments]    ${arg1}    @{arg2}    &{arg3}
    ${value}    Set Variable    ${arg1}

Keyword Call With Variable Error
    [Arguments]    ${used}
    Keyword Call    String with ${variable
    Log    ${used}

Empty Condition Or Var
    [Arguments]    ${used}
    WHILE
        No Operation
    END
    IF
        No Operation
    END
    FOR    In    1  2
        No Operation
    END
    TRY
        Keyword
    EXCEPT  AS
    END
    Log    ${used}

Errors In Arguments
    [Arguments]    ${argument} = value
    Log    ${argument}

Single Underscore Variable
    ${_}    ${var}    Keyword
    FOR    ${_}    IN    @{LIST}
        Log    ${var}
    END
    ${_}    ${var}    Keyword
    @{_} =    Keyword
    @{_} =    Keyword

Keyword With Dict And List Item Assignments
    ${list} =    Create List    one    two    three    four
    ${list}[0] =    Set Variable    first
    ${list}[${1}] =    Set Variable    second
    ${list}[2:3] =    Evaluate    ['third']
    ${list}[-1] =    Set Variable    last

    ${DICTIONARY} =    Create Dictionary    first_name=unknown
    ${DICTIONARY}[first_name] =    Set Variable    John
    ${DICTIONARY}[last_name] =    Set Variable    Doe

Invalid Item Assignment
    ${DICTIONARY    Create Dictionary    first_name=John

Overwritten In IF
    ${variable}    Set Variable    default value
    IF    ${TRUE}
        ${variable}    Set Variable    special value
    ELSE
        ${variable}    Set Variable    special value
    END

Overwritten With VAR
    VAR    ${variable}    value
    VAR    ${variable}    value
    VAR    ${variable2}    value
    VAR    ${variable2} =    value
    ${from_keyword}    Keyword Call
    ${from_keyword2}    Keyword Call
    ${from_keyword3}    Keyword Call
    VAR    ${from_keyword}    ${from_keyword}    scope=GLOBAL  # fine
    VAR    ${from_keyword2}    ${from_keyword2}val  # fine
    VAR    ${from_keyword3}    value  # not fine
    VAR    ${variable3}    value
    VAR    ${variable3}  # missing value
    VAR    $variable  # ignored for invalid variable name
