*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation] doc
    [Tags]  sometag
    Pass
    Keyword
    One More

Test without keyword
    ${a}    ${b}    # no Keyword here!!!


*** Keywords ***
Keyword
    [Documentation]  this is doc
    [Arguments] ${var}
    No Operation
    Pass
    No Operation
    Fail

Keyword With Invalid Documentation
    [Doc Umentation]
