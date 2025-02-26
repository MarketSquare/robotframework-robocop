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
        # TODO even if branch used it, it should be mark as unused. Could be achieved by making
        # add_variables_from_if_to_scope temporarily saving popped variables
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
