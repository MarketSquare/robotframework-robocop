*** Test Cases ***
Leave existing if blocks
    IF    condition
        Keyword
    ELSE IF  condition2
        Keyword2
    ELSE
        Keyword
    END

Single Return Value
    IF    ${condition}
        ${var}    Keyword With ${var}    ${arg}
    END

Multiple Return Values
    IF    ${condition}
        ${var}    ${var2}    Keyword With ${var}    ${arg}
    END

Run keyword if with else if
    IF    ${condition}
        Keyword
    ELSE IF    ${other_condition}
        Other Keyword
    ELSE
        Final Keyword
    END

Run keyword if with else if and args
    IF    ${condition}
        Keyword    a    b    c
    ELSE IF    ${other_condition}
        Other Keyword
    ELSE
        Final Keyword    1    2    ${var}
    END

Run keyword if with else if and return values
    IF    ${condition}
        ${var}    ${var}    Keyword
    ELSE IF    ${other_condition}
        ${var}    ${var}    Other Keyword    ${arg}
    ELSE
        ${var}    ${var}    Final Keyword
    END

Run keyword if with else if and run keywords
    IF    "${var}"=="a"
        First Keyword
        Second Keyword    1    2
    ELSE IF    ${var}==1
        Single Keyword    ${argument}
    ELSE
        Normal Keyword    abc
    END

Run keyword if inside FOR loop
    FOR  ${var}  IN  @{elems}
        IF    ${condition}
            Keyword
        ELSE IF    ${other_condition}
            Other Keyword
        ELSE
            Final Keyword
        END
    END

Run keyword if inside IF
    IF  ${condition}
        IF    ${condition}
            Keyword
        ELSE IF    ${other_condition}
            Other Keyword
        ELSE
            Final Keyword
        END
    END

*** Keywords ***
Test Content Merged Into One Keyword
    IF    condition
        Keyword
    ELSE IF  condition2
        Keyword2
    ELSE
        Keyword
    END

    IF    ${condition}
        Keyword
    ELSE IF    ${other_condition}
        Other Keyword
    ELSE
        Final Keyword
    END

    IF    ${condition}
        Keyword    a    b    c
    ELSE IF    ${other_condition}
        Other Keyword
    ELSE
        Final Keyword    1    2    ${var}
    END

    IF    ${condition}
        ${var}    ${var}    Keyword
    ELSE IF    ${other_condition}
        ${var}    ${var}    Other Keyword    ${arg}
    ELSE
        ${var}    ${var}    Final Keyword
    END

    IF    "${var}"=="a"
        First Keyword
        Second Keyword    1    2
    ELSE IF    ${var}==1
        Single Keyword    ${argument}
    ELSE
        Normal Keyword    abc
    END
