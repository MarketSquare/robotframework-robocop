*** Settings ***
Documentation  doc


*** Test Cases ***
Test.
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keywo.rd
    One More


*** Keywords ***
Keyword?
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With ${em.bedded} Argument
    No Operation
