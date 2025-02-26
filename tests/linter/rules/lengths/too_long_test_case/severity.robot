*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    One More

Golden test
    No Operation

Bit longer test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}
    ...  ${var}






*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
