*** Variables ***
${VARIABLE}    value
${USED_IN_SETUP}    value


*** Keywords ***
No Variables
    Keyword

Used Variable
    ${var}    Keyword
    Log    ${var}

Not Used Variable
    ${var}    Keyword

Mixed Use Variable
    ${var}    ${var2}    Keyword
    ${var}    ${var2}    Keyword  # overwritten, should report there
    Log    ${var}

Assignment Sign
    ${var} =  Keyword

Used In Return
    @{variable}    Keyword
    ...    ${GLOBAL}
    RETURN    ${var_iable}

Used In IF
    ${assign}   IF    $arg2    Keyword
    ${var}
    ...    ${var2}    Keyword
    IF    $var
        Keyword    String with ${var2}
    END
    ${used_in_if}    Keyword
    IF    True
        ${not_used}    Keyword
        Not Relevant Keyword
        Not Relevant Keyword
        ${used_in_branch}    Keyword
    ELSE IF    False
        ${not_used_from_branch}    Keyword    ${used_in_branch}
    ELSE
        Keyword    ${used_in_if}
    END
    IF    nested
        IF    nested-loop
            ${nested_define}    Keyword
            ${nested_define2}    Keyword
            ${nested_define3}    Keyword
        ELSE
            ${nested_define}    Keyword
            ${nested_define2}    Keyword
            ${nested_define3}    Keyword
        END
        Keyword    ${nested_define}
    END
    Keyword    ${nested_define2}

Not Used From FOR
    FOR    ${var}    IN    1  2  3
        Keyword    ${VAR}
    END
    FOR    ${var}    IN    1  2  3
        Keyword
    END
    FOR    ${_}    IN    1  2  3
        Keyword
    END

Single Underscore Not Used
    ${_}    ${var}    Keyword
    Log    ${var}

While Limit
    ${used_var}    Get Loop Limit
    WHILE    $condition    limit=${used_var} sec
        Log    In loop.
    END

*** Test Cases ***
Test with template
    [Template]    Template Keyword
    FOR    ${category}    IN    @{CATEGORIES}
        ${category}
    END

Test with template - not used
    [Template]    Template Keyword
    FOR    ${category}    IN    @{CATEGORIES}
        constant
    END

Simple Operations
    ${sum}    Calculate    ${random}
    ${var}    Set Variable    ${sum%11}
    ${var}    Set Variable    ${sum + 11}
    ${var}    Set Variable    ${sum - 11}
    ${var}    Set Variable    ${sum * 11}
    Log    ${var}

Test With Dict And List Item Assignments
    ${list} =    Create List    one    two    three    four
    ${list}[0] =    Set Variable    first
    ${list}[${1}] =    Set Variable    second
    ${list}[2:3] =    Evaluate    ['third']
    ${list}[-1] =    Set Variable    last
    Log    ${list}

    ${DICTIONARY} =    Create Dictionary    first_name=unknown
    ${DICTIONARY}[first_name] =    Set Variable    John
    ${DICTIONARY}[last_name] =    Set Variable    Doe
    Log    ${dictionary}

Invalid Item Assignment
    ${DICTIONARY    Create Dictionary    first_name=John

Prepare Item With Attribute
    ${item}    Get Item
    ${item.x}    Set Variable    abc
    RETURN    ${item}

Update Item With Attribute
    ${item}    Get Item
    ${item.x}    Set Variable    abc

Use Item With Attribute
    ${item}    Prepare Item
    Log    ${item.x}

Use Item With Method
    ${string}    Set Variable    string
    ${lower_string}    Set Variable    ${string.lower()}
    Log    ${lower_string}

Inline If - Overwritten Variable
    ${var}    Set Variable    default
    ${var}    IF    condition    Use    ${var}

InlineIf - Assign With The Same Name As Arg
    ${assign}    IF    condition    Do Nothing    ELSE    Use    ${assign}

Unused With VAR
    VAR    ${not_used}    value
    VAR    ${not_used_global}    value    scope=TEST
    VAR    ${used_in_kw}    value
    Keyword Call    ${used_in_kw}
    VAR    ${used_in_var}    value
    VAR    ${used_in_var}    ${used_in_var}    scope=SUITE
    VAR    ${used_without_sign}=    value
    Keyword Call    ${used_without_sign}
    VAR    ${variable}  # missing value
    VAR    $variable  # ignored for invalid variable name

Unused In Setup
    [Setup]    Keyword Setup    ${used_in_setup}
    Step

ELIF use same name variable
    IF    condition
        ${var}    Keyword
    ELSE IF    ${var}
        Log    Should be raised for var.
    END

Used in one branch
    IF    condition
        ${var}    Keyword
    ELSE IF    condition2
        ${var}    Keyword
        Log    ${var}
    END
    IF    condition
        ${var2}    Keyword
        Log    ${var2}
    ELSE IF    condition2
        ${var2}    Keyword
    END

Used in one branch and header
    IF    condition
        ${var}    Keyword
    ELSE IF    ${var}
        ${var}    Keyword
        Log    ${var}
    END
    IF    condition
        ${var2}    Keyword
        Log    ${var2}
    ELSE IF    ${var2}
        ${var2}    Keyword  # declared, but used only in one branch
    END

Used in one branch and after IF
    IF    condition
        ${var}    Keyword
    ELSE IF    ${var}
        ${var}    Keyword
        Log    ${var}
    END
    Log    ${var}

Double FOR loops
    [Arguments]    ${initial_token}
    ...    ${retries}=5
    # Bug: 1148
    VAR    ${continuation_token}    ${initial_token}

    FOR    ${i}    IN RANGE    ${{ int($retries)+1 }}
        ${response} =    Get Events    ${continuation_token}
        FOR    ${_}    IN    @{response}[events]
            # Do stuff
            No Operation
        END

        IF    $i < int($retries)
            VAR    ${continuation_token}    ${response}[continuationToken]
        END
    END

Use variable inside second FOR
    FOR    ${x}    IN RANGE    10
        ${calculation1}    Perform Calculation
        FOR    ${y}    IN RANGE    5
             Increment    ${calculation1}    ${x}   ${y}
             Increment    ${calculation2}    ${x}   ${y}
        END
        ${calculation2}    Perform Calculation
    END

Used in EXCEPT branch
    ${var1}    ${var2}    Get Variables
    TRY
        May Fail    ${var1}
    EXCEPT    ${var2}
        No Operation
    END
