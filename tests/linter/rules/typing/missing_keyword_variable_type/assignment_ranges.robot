*** Variables ***
${SECTION}=    value
${SPACED_SECTION} =    value

*** Test Cases ***
Test Assignments
    VAR    ${var}=    value
    ${spaced} =    Set Variable    value
    ${unspaced}=    Set Variable    value
    ${without}    Set Variable    value

*** Keywords ***
Keyword Assignments
    VAR    ${var}=    value
    ${spaced} =    Set Variable    value
    ${unspaced}=    Set Variable    value
    ${without}    Set Variable    value
    ${items}[0] =    Set Variable    value
