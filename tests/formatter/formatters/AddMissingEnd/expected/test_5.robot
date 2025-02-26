*** Keywords ***
Inline IF
    IF    $cond    Keyword
    IF    $cond    Keyword    ELSE    Keyword2    ${var}

WHILE
    WHILE    $cond
        Keyword
        # comment
    END
    Keyword 2

TRY EXCEPT
    TRY
        Some Keyword
    EXCEPT    Error message    # Try matching this first.
        IF    $cond    Keyword
    END
