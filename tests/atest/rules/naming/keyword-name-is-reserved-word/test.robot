*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    For
    End
    Fail
    Run Keyword If  ${True}  Keyword
    ...  else  Keyword2

Run Keyword If
    [Arguments]    ${name}    ${condition}    @{args}
    BuiltIn.Run Keyword If    ${name}    ${condition}    @{args}  else if  Keyword
