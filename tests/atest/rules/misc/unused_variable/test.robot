*** Variables ***
${VARIABLE}    value


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
