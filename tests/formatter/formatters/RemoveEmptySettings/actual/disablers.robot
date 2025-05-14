*** Settings ***
# robocop: fmt: off
Metadata    doc=1


*** Test Cases ***
Test
    [Tags]    tag
    Keyword
# robocop: fmt: off
Test 2
    [Setup]    Keyword
    [Template]    Keyword
    [Timeout]    1min
    Keyword

Test 3
    Keyword



*** Keywords ***
Keyword
    [Arguments]    ${arg}
    Keyword
# robocop: fmt: off
Keyword 2
    Keyword
    [Return]    stuff
