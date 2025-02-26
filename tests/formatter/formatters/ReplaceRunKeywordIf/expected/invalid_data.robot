*** Test Cases ***
No condition and keyword with arg
    IF    Keyword
        Run Keyword    ${arg}
    END

No condition and keyword without arg
    Run Keyword If  Keyword

No arguments
    Run Keyword If

Empty ELSE branch
    Run Keyword If  ${condition}  Keyword
    ...  ELSE

    Run Keyword If  ${condition}  Keyword
    ...  ELSE IF

Invalid new line mark
    IF    ${condition}
        Keyword
    END
    ..  Keyword

    IF    ${condition
        Keyword
    END
    ... Keyword

Not closed for loop
    FOR  ${var}  IN  @{elems}
        IF    ${condition}
            Keyword
        END

Not closes if
    IF  ${condition}
        IF    ${condition}
            Keyword
        END
