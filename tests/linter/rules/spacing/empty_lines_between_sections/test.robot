*** Settings ***
Documentation  doc



*** Variables ***
${MY_VAR}    1

# some comment
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
    Fail
*** Comments ***
Blah Blah Blah
