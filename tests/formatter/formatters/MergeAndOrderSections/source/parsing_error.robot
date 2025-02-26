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
    IF    ${condition}
        Keyword
    ELse IF   ${condition}
        Keyword
    END
    IF    ${condition}
        Keyword
    ELSE IF   ${condition}
        Keyword
    ElSE
        Keyword
    END
    IF    ${condition}    ${condition}
        Keyword
    END
    IF    ${condition} ==
    \   ${flag}
        Keyword
    END

For Loop
    FOR  IN RANGE  10
        Keyword
    END
    FOR  ${var}  IN  @{list}
    END
    FOR  ${var}  IN RANGE
        Keyword
    END
    FOR  ${var}  IN RANGE  10
        Keyword
    FOR  ${var}  @{list}
        Keyword
    END