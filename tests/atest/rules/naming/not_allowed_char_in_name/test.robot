\*** Settings ***
Documentation  doc


*** Test Cases ***
Test.
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keywo.rd
    One More


*** Keywords ***
Keyword${?
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

Keyword With ${em.bedded} Argument
    No Operation

Keyword With ${em.bedded} Two ${second.Argument} Argument
    No Operation

Keyword ${?} Should Not Warn
    No Operation

Keyword Escaped \${?} Should Warn
    [Documentation]  this is doc
    No Operation
