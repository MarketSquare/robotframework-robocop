*** Settings ***
Suite Setup    Run Keyword If    ${condition}    Keyword


*** Test Cases ***
Simple Run Keyword If
    IF    ${condition}
        Keyword    ${arg}
    END

Run Keyword If With Else If And Else
    IF    ${condition}
        Keyword
    ELSE IF    ${other_condition}
        Other Keyword    ${arg}
    ELSE
        Final Keyword
    END

Run Keyword If With Assign
    IF    ${condition}
        ${var}    Keyword    ${arg}
    ELSE
        ${var}    Keyword2
    END

Run Keyword If With Run Keywords
    IF    ${condition}
        First Keyword
        Second Keyword    1    2
    END

Simple Run Keyword Unless
    IF    not (${condition})
        Keyword    ${arg}
    END

Run Keyword Unless With Assign
    IF    not (${condition})
        ${var}    Keyword    ${arg}
    ELSE
        ${var}    Set Variable    ${None}
    END

Nested In For And If
    FOR    ${item}    IN    @{items}
        IF    ${condition}
            IF    ${other}
                Keyword
            END
        END
    END

Empty Run Keyword If
    Run Keyword If

Templated Test
    [Template]    Run Keyword Unless
