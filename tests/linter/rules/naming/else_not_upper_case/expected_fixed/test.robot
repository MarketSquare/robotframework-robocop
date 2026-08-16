*** Test Cases ***
Test
    No Operation
    If  ${condition}    Keyword     END
    IF    ${condition}    Keyword
    ELSE if    Keyword2
    ELse    Keyword3
    End
    IF    ${condition}
        Keyword
    ELSE IF   ${condition}
        Keyword
    END
    IF    ${condition}
        Keyword
    ELSE IF   ${condition}
        Keyword
    ELSE
        Keyword
    END
    IF    ${condition}
        FOR  ${i}  IN  @{list}
            Keyword
        End
    END

No Keyword Name
    IF  Keyword
        ${argument}
    END
