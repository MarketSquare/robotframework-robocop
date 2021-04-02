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
    FOR  ${var}  IN RANGE  10
        FOR  ${var2}  IN  a  b  c
            Log  ${var2}
        END
    END
    No Operation
    Fail
