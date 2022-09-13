*** Settings ***
Documentation  doc


*** Test Cases ***
Long test case
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    Keyword
    One More


Test case with one keyword call
    Skip

Test case with no keyword calls

Test case with settings and no keyword calls
    [Tags]    smoke
    [Setup]    Keyword
    [Timeout]    1 min
    [Documentation]    doc


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
