*** SETTINGS ***
Documentation  doc


*** Variables ***
${var}  1


*** Test Case ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More


*** keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail

*** Comment ***