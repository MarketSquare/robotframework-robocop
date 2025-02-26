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
    [Arguments]    ${var}

Two Arguments
    [Arguments]    ${var}    ${var2}

No Arguments
    Log    ${EMPTY}

Empty Arguments
    [Arguments]

Return
    RETURN    ${var}

Return in block
    IF    $condition
        FOR    ${var}    IN RANGE    10
            IF    $var    RETURN    ${other_value}    ${multiple}
        END
    END

[Return]
     Step
     [Return]    ${var}

Double [Return]
     Step
     [Return]    ${var}
     [Return]    ${var}
     ...    ${var2}

Arguments And Return
    [Arguments]    ${var}
    ...    ${var2}
    RETURN    ${var}

One Required And One With Default
    [Arguments]    ${required}    ${optional}=default
    Log    Required: ${required}
    Log    Optional: ${optional}

Default Based On Earlier Argument
    [Arguments]    ${a}    ${b}=${a}    ${c}=${a} and ${b}
    Should Be Equal    ${a}    ${b}
    Should Be Equal    ${c}    ${a} and ${b}

Existing documentation
    [Documentation]    Overwrite if needed.
    Step

Embedded ${var} variable
    Step

Two ${embedded:pattern} variables ${embedded2}
    Step
