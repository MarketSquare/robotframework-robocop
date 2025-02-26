*** Settings ***
Documentation  doc


*** Test Cases ***
Test
    [Documentation]  doc
    [Tags]  sometag
    Pass
    Keyword
    One More

Test without keyword
    ${a}    ${b}    # no Keyword here!!!


*** Keywords ***
Keyword
    [Documentation]  this is doc
    No Operation
    Pass
    No Operation
    Fail
    RETURN    ${var}  2  4  4  5

Keyword 2
    Return From Keyword  ${var}  2  4  4  5

Keyword 3
    FOR  ${var}  IN RANGE  10
        BuiltIn.Return From Keyword If    ${condition}==${True}    ${var}  2  4  4  5
    END

Try Except While
    WHILE    $condition
        TRY
            RETURN    ${var}  2  4  4  5
        EXCEPT
            RETURN    ${var}  2  4  4  5
        FINALLY
            RETURN    ${var}  2  4  4  5
        ELSE
            RETURN    ${var}  2  4  4  5
        END
        RETURN    ${var}
    END
    [Return]         ${var}  2  4  4  5
