*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    ...              Tags:  tagORtag2  tagor
    No Operation
    Pass
    No Operation
    Fail
