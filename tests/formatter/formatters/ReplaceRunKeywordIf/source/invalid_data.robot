*** Test Cases ***
No condition and keyword with arg
    Run Keyword If  Keyword  ${arg}

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
    Run Keyword If  ${condition}  Keyword
    ..  Keyword

    Run Keyword If  ${condition  Keyword
    ... Keyword

Not closed for loop
    FOR  ${var}  IN  @{elems}
        Run Keyword If  ${condition}  Keyword

Not closes if
    IF  ${condition}
        Run Keyword If  ${condition}  Keyword
