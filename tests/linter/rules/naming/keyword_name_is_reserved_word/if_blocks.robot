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
    IF    ${condition}
        FOR  ${i}  IN  @{list}
            Keyword
        End
    END