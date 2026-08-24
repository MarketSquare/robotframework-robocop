*** Settings ***
Suite Setup    Run Keyword If    ${condition}    Keyword


*** Test Cases ***
Simple Run Keyword If
    Run Keyword If    ${condition}    Keyword    ${arg}

Run Keyword If With Else If And Else
    Run Keyword If    ${condition}    Keyword
    ...    ELSE IF    ${other_condition}    Other Keyword    ${arg}
    ...    ELSE    Final Keyword

Run Keyword If With Assign
    ${var}    Run Keyword If    ${condition}    Keyword    ${arg}    ELSE    Keyword2

Run Keyword If With Run Keywords
    Run Keyword If    ${condition}    Run Keywords    First Keyword    AND    Second Keyword    1    2

Simple Run Keyword Unless
    Run Keyword Unless    ${condition}    Keyword    ${arg}

Run Keyword Unless With Assign
    ${var}    Run Keyword Unless    ${condition}    Keyword    ${arg}

Nested In For And If
    FOR    ${item}    IN    @{items}
        IF    ${condition}
            Run Keyword If    ${other}    Keyword
        END
    END

Empty Run Keyword If
    Run Keyword If

Templated Test
    [Template]    Run Keyword Unless
