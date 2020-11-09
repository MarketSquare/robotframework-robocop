*** Settings ***
Documentation  doc
Force Tags  tagORtag2  tagor
Default Tags  tagORtag2  tagor


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  tagORtag2  tagor
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
