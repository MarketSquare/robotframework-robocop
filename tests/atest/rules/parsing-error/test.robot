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
    [Argument]
    No Operation
    Pass
    No Operation
    Fail
    IF    ${condition}
        Keyword
    End
    IF    ${condition}
        Keyword
    ELSE IF  ${condition}    Empty Body
    END
