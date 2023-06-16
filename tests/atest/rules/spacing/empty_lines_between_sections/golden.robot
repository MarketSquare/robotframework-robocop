*** Settings ***


*** Variables ***
${MY_VAR}    1


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More



# some comment
