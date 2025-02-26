*** Test Cases ***
Missing condition
    IF
        Keyword
    END
    IF
        Keyword
    END

Two conditions
    IF    ${condition}    Keyword
        Keyword
    END
    IF    ${condition}    Keyword
        Keyword
    END
