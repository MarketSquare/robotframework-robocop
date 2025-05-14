*** Settings ***
Documentation    Suite documentation should not be changed.


*** Test Cases ***
Test without documentation
    No Operation

Test with documentation
    [Documentation]    Should not be changed.
    No Operation


*** Keywords ***
Single Argument
    [Documentation]    Single Argument
    ...
    ...    Arguments:
    ...        ${var}: 
    [Arguments]    ${var}

Two Arguments
    [Documentation]    Two Arguments
    ...
    ...    Arguments:
    ...        ${var}: 
    ...        ${var2}: 
    [Arguments]    ${var}    ${var2}

No Arguments
    [Documentation]    No Arguments
    Log    ${EMPTY}

Empty Arguments
    [Documentation]    Empty Arguments
    [Arguments]

Return
    [Documentation]    Return
    ...
    ...    Returned values:
    ...        ${var}: 
    RETURN    ${var}

Return in block
    [Documentation]    Return in block
    ...
    ...    Returned values:
    ...        ${other_value}: 
    ...        ${multiple}: 
    IF    $condition
        FOR    ${var}    IN RANGE    10
            IF    $var    RETURN    ${other_value}    ${multiple}
        END
    END

[Return]
    [Documentation]    [Return]
    ...
    ...    Returned values:
    ...        ${var}: 
     Step
     [Return]    ${var}

Double [Return]
    [Documentation]    Double [Return]
    ...
    ...    Returned values:
    ...        ${var}: 
     Step
     [Return]    ${var}
     [Return]    ${var}
     ...    ${var2}

Arguments And Return
    [Documentation]    Arguments And Return
    ...
    ...    Arguments:
    ...        ${var}: 
    ...        ${var2}: 
    ...
    ...    Returned values:
    ...        ${var}: 
    [Arguments]    ${var}
    ...    ${var2}
    RETURN    ${var}

One Required And One With Default
    [Documentation]    One Required And One With Default
    ...
    ...    Arguments:
    ...        ${required}: 
    ...        ${optional} = 'default': 
    [Arguments]    ${required}    ${optional}=default
    Log    Required: ${required}
    Log    Optional: ${optional}

Default Based On Earlier Argument
    [Documentation]    Default Based On Earlier Argument
    ...
    ...    Arguments:
    ...        ${a}: 
    ...        ${b} = '${a}': 
    ...        ${c} = '${a} and ${b}': 
    [Arguments]    ${a}    ${b}=${a}    ${c}=${a} and ${b}
    Should Be Equal    ${a}    ${b}
    Should Be Equal    ${c}    ${a} and ${b}

Existing documentation
    [Documentation]    Overwrite if needed.
    Step

Embedded ${var} variable
    [Documentation]    Embedded ${var} variable
    ...
    ...    Arguments:
    ...        ${var}: 
    Step

Two ${embedded:pattern} variables ${embedded2}
    [Documentation]    Two ${embedded:pattern} variables ${embedded2}
    ...
    ...    Arguments:
    ...        ${embedded:pattern}: 
    ...        ${embedded2}: 
    Step
