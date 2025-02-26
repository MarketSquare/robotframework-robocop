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
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${var}: <description>
    [Arguments]    ${var}

Two Arguments
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${var}: <description>
    ...        ${var2}: <description>
    [Arguments]    ${var}    ${var2}

No Arguments
    [Documentation]    Short description.
    Log    ${EMPTY}

Empty Arguments
    [Documentation]    Short description.
    [Arguments]

Return
    [Documentation]    Short description.
    RETURN    ${var}

Return in block
    [Documentation]    Short description.
    IF    $condition
        FOR    ${var}    IN RANGE    10
            IF    $var    RETURN    ${other_value}    ${multiple}
        END
    END

[Return]
    [Documentation]    Short description.
    ...
    ...    Returns:
    ...        ${var}: <description>
     Step
     [Return]    ${var}

Double [Return]
    [Documentation]    Short description.
    ...
    ...    Returns:
    ...        ${var}: <description>
     Step
     [Return]    ${var}
     [Return]    ${var}
     ...    ${var2}

Arguments And Return
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${var}: <description>
    ...        ${var2}: <description>
    [Arguments]    ${var}
    ...    ${var2}
    RETURN    ${var}

One Required And One With Default
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${required}: <description>
    ...        ${optional}: <description>
    [Arguments]    ${required}    ${optional}=default
    Log    Required: ${required}
    Log    Optional: ${optional}

Default Based On Earlier Argument
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${a}: <description>
    ...        ${b}: <description>
    ...        ${c}: <description>
    [Arguments]    ${a}    ${b}=${a}    ${c}=${a} and ${b}
    Should Be Equal    ${a}    ${b}
    Should Be Equal    ${c}    ${a} and ${b}

Existing documentation
    [Documentation]    Short description.    Overwrite if needed.
    Step

Embedded ${var} variable
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${var}: <description>
    Step

Two ${embedded:pattern} variables ${embedded2}
    [Documentation]    Short description.
    ...
    ...    Args:
    ...        ${embedded:pattern}: <description>
    ...        ${embedded2}: <description>
    Step
